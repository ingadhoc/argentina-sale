##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.fields import Command
from odoo.tests import tagged

EXPO_POS_SYSTEMS = ["FEERCEL", "FEEWS", "FEERCELP"]


@tagged("post_install", "-at_install")
class TestL10nArSaleOrderType(TestArCommon):
    """What the sale order type adds for Argentinian companies.

    Covers: forcing VAT discrimination from the type, keeping the type journal
    instead of the export one, printing on the Argentinian report the header
    contact that sale_order_type_report_partner adds to the type, and offering
    the discrimination field only for Argentinian companies.
    """

    @classmethod
    def get_default_groups(cls):
        return super().get_default_groups() | cls.env.ref("sales_team.group_sale_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # exception rules of other modules leave the order in draft on action_confirm
        if cls.env["sale.order"]._fields.get("ignore_exception"):
            cls.env["exception.rule"].sudo().search([("active", "=", True)]).write({"active": False})
        cls.product_iva_21.invoice_policy = "order"
        cls.sale_type = cls.env["sale.order.type"].create({"name": "Unit test type"})
        cls.preprinted_journal = cls._create_journal("preprinted")

    def _create_order(self, partner, **type_vals):
        self.sale_type.write(type_vals)
        return self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "type_id": self.sale_type.id,
                "order_line": [
                    Command.create({"product_id": self.product_iva_21.id, "product_uom_qty": 1.0, "price_unit": 100.0})
                ],
            }
        )

    def _render_sale_order(self, order):
        return self.env["ir.actions.report"]._render_qweb_html("sale.report_saleorder", order.ids)[0].decode()

    def test_vat_discriminated_follows_the_order_type(self):
        with self.subTest("el tipo que discrimina fuerza el IVA discriminado"):
            order = self._create_order(self.res_partner_gritti_mono, discriminate_taxes="yes")
            self.assertTrue(order.vat_discriminated)
        with self.subTest("el tipo que no discrimina lo fuerza en contra"):
            order = self._create_order(self.res_partner_adhoc, discriminate_taxes="no")
            self.assertFalse(order.vat_discriminated)
        with self.subTest("el tipo sin definir deja decidir la responsabilidad del cliente"):
            self.assertTrue(self._create_order(self.res_partner_adhoc, discriminate_taxes=False).vat_discriminated)
            self.assertFalse(
                self._create_order(self.res_partner_gritti_mono, discriminate_taxes=False).vat_discriminated
            )

    def test_order_type_journal_wins_over_the_export_journal(self):
        with self.subTest("sin diario propio la factura sale en el de exportación"):
            order = self._create_order(self.res_partner_barcelona_food, journal_id=False)
            order.action_confirm()
            invoice = order._create_invoices()
            self.assertIn(invoice.journal_id.l10n_ar_afip_pos_system, EXPO_POS_SYSTEMS)
        with self.subTest("con diario propio la factura sale en ese diario"):
            order = self._create_order(self.res_partner_barcelona_food, journal_id=self.preprinted_journal.id)
            order.action_confirm()
            invoice = order._create_invoices()
            self.assertEqual(invoice.journal_id, self.preprinted_journal)

    def test_report_header_takes_the_partner_of_the_order_type(self):
        header_partner = self.env["res.partner"].create({"name": "Header Contact Of The Type"})
        order = self._create_order(self.res_partner_adhoc, report_partner_id=False)
        without = self._render_sale_order(order)
        self.assertIn("VAT Cond", without, "the order is not using the Argentinian sale order template")
        self.assertNotIn(header_partner.name, without)
        self.sale_type.report_partner_id = header_partner
        order.invalidate_recordset()
        self.assertIn(header_partner.name, self._render_sale_order(order))

    def test_discriminate_taxes_is_only_offered_in_argentina(self):
        with self.subTest("el tipo de una compañía argentina ofrece el campo"):
            ar_type = self.env["sale.order.type"].create({"name": "AR type", "company_id": self.company_ri.id})
            self.assertIn("AR", ar_type.fiscal_country_codes)
        with self.subTest("el tipo de una compañía de otro país no lo ofrece"):
            spain = self.env.ref("base.es")
            foreign_company = self.env["res.company"].create(
                {
                    "name": "Foreign Co",
                    "country_id": spain.id,
                    # the OBA stack checks that the currency matches the country
                    "currency_id": spain.currency_id.id,
                }
            )
            foreign_type = self.env["sale.order.type"].create(
                {"name": "Foreign type", "company_id": foreign_company.id}
            )
            self.assertNotIn("AR", foreign_type.fiscal_country_codes or "")
