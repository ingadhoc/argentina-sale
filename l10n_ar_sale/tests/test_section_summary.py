##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.fields import Command
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSectionSummary(TestArCommon):
    @classmethod
    def get_default_groups(cls):
        return super().get_default_groups() | cls.quick_ref("sales_team.group_sale_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vat_tax = cls.product_iva_21.taxes_id.filtered(lambda tax: tax.company_id == cls.company_ri)
        cls.vat_tax.write({"name": "VAT 21% Name", "invoice_label": "VAT 21% Label"})
        cls.perception_tax = cls.tax_perc_iibb.copy(
            {"name": "Perception Name", "invoice_label": "Perception Label", "amount": 3.0, "active": True}
        )

    def _create_order(self, partner):
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    Command.create({"display_type": "line_section", "name": "Section", "collapse_composition": True}),
                    Command.create(
                        {
                            "product_id": self.product_iva_21.id,
                            "price_unit": 100.0,
                            "tax_ids": [Command.set(self.vat_tax.ids)],
                        }
                    ),
                    Command.create(
                        {
                            "product_id": self.product_iva_21.id,
                            "price_unit": 200.0,
                            "tax_ids": [Command.set((self.vat_tax | self.perception_tax).ids)],
                        }
                    ),
                ],
            }
        )
        return order, order.order_line.filtered(lambda line: line.display_type == "line_section")

    def test_vat_discriminated_section_shows_tax_labels(self):
        order, section = self._create_order(self.res_partner_adhoc)
        self.assertTrue(order.vat_discriminated)
        summary = section._get_grouped_section_summary(display_taxes=True)
        self.assertCountEqual(
            [(sorted(row["tax_labels"]), row["price_subtotal"]) for row in summary],
            [(["VAT 21% Label"], 100.0), (["Perception Label", "VAT 21% Label"], 200.0)],
        )
        self.assertEqual(section._get_section_totals("price_subtotal"), 300.0)

    def test_vat_not_discriminated_section_includes_vat(self):
        order, section = self._create_order(self.partner_cf)
        self.assertFalse(order.vat_discriminated)
        summary = section._get_grouped_section_summary(display_taxes=False)
        self.assertEqual(len(summary), 1)
        self.assertFalse(summary[0]["tax_labels"])
        self.assertEqual(summary[0]["price_subtotal"], 363.0)
        self.assertEqual(section._get_section_totals("price_subtotal"), 363.0)
