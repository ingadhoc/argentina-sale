##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCreateInvoices(TestArCommon):
    @classmethod
    def get_default_groups(cls):
        return super().get_default_groups() | cls.env.ref("sales_team.group_sale_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # exception rules of other modules leave the order in draft on action_confirm
        if cls.env["sale.order"]._fields.get("ignore_exception"):
            cls.env["exception.rule"].sudo().search([("active", "=", True)]).write({"active": False})

    def _create_confirmed_order(self):
        self.product_iva_21.invoice_policy = "order"
        order = self.env["sale.order"].create(
            {
                "partner_id": self.res_partner_adhoc.id,
                "order_line": [
                    Command.create({"product_id": self.product_iva_21.id, "product_uom_qty": 2.0, "price_unit": 100.0}),
                ],
            }
        )
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        return order

    def test_refuse_invoiced_order(self):
        order = self._create_confirmed_order()
        order._create_invoices()
        self.assertEqual(order.invoice_status, "invoiced")
        with self.assertRaises(UserError):
            order._create_invoices()

    def test_no_raise_when_context_says_so(self):
        # payment transactions invoice paid orders with this context and must not fail
        order = self._create_confirmed_order()
        order._create_invoices()
        invoices = order.with_context(raise_if_nothing_to_invoice=False)._create_invoices()
        self.assertFalse(invoices)

    def test_refuse_no_status_without_invoiceable_lines(self):
        order = self._create_confirmed_order()
        order._create_invoices()
        self.env.cr.execute("UPDATE sale_order SET invoice_status = 'no' WHERE id = %s", [order.id])
        order.invalidate_recordset(["invoice_status"])
        with self.assertRaises(UserError):
            order._create_invoices()

    def test_invoice_no_status_with_invoiceable_lines(self):
        order = self._create_confirmed_order()
        # "no" is the fallback status, it can be left on an order that still has lines to invoice
        self.env.cr.execute("UPDATE sale_order SET invoice_status = 'no' WHERE id = %s", [order.id])
        order.invalidate_recordset(["invoice_status"])
        invoices = order._create_invoices()
        self.assertEqual(invoices.invoice_line_ids.quantity, 2.0)

    def test_invoice_order_with_status_added_by_other_module(self):
        order = self._create_confirmed_order()
        # a status added with selection_add by another module, with quantities left to invoice
        self.env.cr.execute("UPDATE sale_order SET invoice_status = 'partial' WHERE id = %s", [order.id])
        order.invalidate_recordset(["invoice_status"])
        invoices = order._create_invoices()
        self.assertEqual(invoices.invoice_line_ids.quantity, 2.0)
