##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.fields import Command
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPerceptionRecompute(TestArCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the chart perception comes with amount 0 and _l10n_ar_add_taxes drops it
        cls.perception_tax = cls.tax_perc_iibb.copy({"name": "Percepcion IIBB Test 3%", "amount": 3.0, "active": True})
        cls.fiscal_position = cls.env["account.fiscal.position"].create(
            {
                "name": "Percepcion IIBB Test",
                "company_id": cls.company_ri.id,
                "l10n_ar_tax_ids": [
                    Command.create({"tax_type": "perception", "default_tax_id": cls.perception_tax.id}),
                ],
            }
        )

    def test_recompute_skips_section_and_note_lines(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.res_partner_adhoc.id,
                "fiscal_position_id": self.fiscal_position.id,
                "order_line": [
                    Command.create({"display_type": "line_section", "name": "Section"}),
                    Command.create({"product_id": self.product_iva_21.id, "product_uom_qty": 1.0, "price_unit": 100.0}),
                    Command.create({"display_type": "line_note", "name": "Note"}),
                ],
            }
        )
        product_line = order.order_line.filtered(lambda line: not line.display_type)
        self.assertIn(self.perception_tax, product_line.tax_id)
        self.assertFalse((order.order_line - product_line).tax_id)

        # same check for the onchange on partner / date
        order._l10n_ar_recompute_fiscal_position_taxes()
        self.assertIn(self.perception_tax, product_line.tax_id)
        self.assertFalse((order.order_line - product_line).tax_id)

        copied_order = order.copy()
        copied_product_line = copied_order.order_line.filtered(lambda line: not line.display_type)
        self.assertIn(self.perception_tax, copied_product_line.tax_id)
        self.assertFalse((copied_order.order_line - copied_product_line).tax_id)

    def test_recompute_cleans_perceptions_left_on_notes(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.res_partner_adhoc.id,
                "fiscal_position_id": self.fiscal_position.id,
                "order_line": [
                    Command.create({"product_id": self.product_iva_21.id, "product_uom_qty": 1.0, "price_unit": 100.0}),
                ],
            }
        )
        # notes saved with a perception before the fix
        note = self.env["sale.order.line"].create({"order_id": order.id, "display_type": "line_note", "name": "Note"})
        note.tax_id = self.perception_tax
        self.assertEqual(note.tax_id, self.perception_tax)

        copied_order = order.copy()
        copied_note = copied_order.order_line.filtered("display_type")
        self.assertFalse(copied_note.tax_id)

        order._l10n_ar_recompute_fiscal_position_taxes()
        self.assertFalse(note.tax_id)
