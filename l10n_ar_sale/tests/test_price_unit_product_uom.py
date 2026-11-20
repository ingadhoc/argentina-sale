##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.fields import Command
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestPriceUnitProductUom(TestArCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("sales_team.group_sale_manager")

        cls.vat_21 = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company_ri.id),
                ("type_tax_use", "=", "sale"),
                ("tax_group_id.l10n_ar_vat_afip_code", "=", "5"),
                ("amount", "=", 21.0),
            ],
            limit=1,
        )
        assert cls.vat_21, "No se encontró el IVA 21% de venta de la compañía de prueba"

        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.uom_box_15 = cls.env["uom.uom"].create(
            {"name": "Box 15 kg", "relative_factor": 15.0, "relative_uom_id": cls.uom_kg.id}
        )
        cls.product_kg = cls.env["product.product"].create(
            {
                "name": "Welding wire",
                "type": "consu",
                "list_price": 4.522,
                "uom_id": cls.uom_kg.id,
                "uom_ids": [Command.set([cls.uom_box_15.id])],
                "taxes_id": [Command.set(cls.vat_21.ids)],
            }
        )

    def _create_line(self, partner, price_unit=67.83, document_tax_mode=None):
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "company_id": self.company_ri.id,
                **({"document_tax_mode": document_tax_mode} if document_tax_mode else {}),
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_kg.id,
                            "product_uom_id": self.uom_box_15.id,
                            "product_uom_qty": 5.0,
                            "price_unit": price_unit,
                            "tax_ids": [Command.set(self.vat_21.ids)],
                        }
                    )
                ],
            }
        )
        return order.order_line

    def test_price_without_vat_when_the_customer_discriminates_it(self):
        line = self._create_line(self.res_partner_adhoc)

        self.assertTrue(line.order_id.vat_discriminated)
        self.assertAlmostEqual(line.price_unit_product_uom, 4.522)

    def test_price_with_vat_when_the_customer_does_not_discriminate_it(self):
        line = self._create_line(self.partner_cf)

        self.assertFalse(line.order_id.vat_discriminated)
        self.assertAlmostEqual(line.price_unit_product_uom, 5.4716)

    def test_price_matches_the_printed_quotation(self):
        line = self._create_line(self.partner_cf)

        self.env["ir.config_parameter"].sudo().set_bool("sale_ux.report_in_product_uom", True)
        values = line._get_report_product_uom_values()

        self.assertAlmostEqual(values["price_unit"], line.price_unit_product_uom, places=4)

    def test_editing_the_price_takes_the_vat_out(self):
        # Another starting price on purpose: at 67.83 the line already shows 5.4716 per kg,
        # so the assertion would pass even if the onchange did nothing
        line = self._create_line(self.partner_cf, price_unit=60.0)

        with Form(line.order_id) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.price_unit_product_uom = 5.4716

        self.assertAlmostEqual(line.price_unit, 67.83)

    def test_vat_included_in_the_price_is_not_taken_out_twice(self):
        """With a price-included VAT the unit price already holds it, so it stays as is."""
        vat_included = self.vat_21.copy({"name": "IVA 21 incluido", "price_include_override": "tax_included"})
        line = self._create_line(self.partner_cf, price_unit=121.0)
        line.tax_ids = vat_included

        self.assertAlmostEqual(line.price_unit_product_uom, 121.0 / 15.0, places=4)

        with Form(line.order_id) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.price_unit_product_uom = 121.0 / 15.0

        self.assertAlmostEqual(line.price_unit, 121.0, places=2)

    def test_fixed_tax_is_applied_once_per_unit(self):
        """Ten pesos per unit on five boxes is ten pesos on each, not ten on the line."""
        internal_group = self.env["account.tax.group"].create({"name": "Impuestos internos"})
        fixed_tax = self.env["account.tax"].create(
            {
                "name": "Impuesto fijo",
                "company_id": self.company_ri.id,
                "tax_group_id": internal_group.id,
                "type_tax_use": "sale",
                "amount_type": "fixed",
                "amount": 10.0,
                "price_include_override": "tax_included",
            }
        )
        line = self._create_line(self.res_partner_adhoc, price_unit=110.0)
        # The VAT stays on the line: l10n_ar_sale wants exactly one VAT tax per line
        line.tax_ids = self.vat_21 + fixed_tax

        self.assertFalse(fixed_tax.tax_group_id.l10n_ar_vat_afip_code)
        # 110 a box with 10 of tax inside is 100 net a box, which is 100 / 15 a kg
        self.assertAlmostEqual(line.price_unit_product_uom, 100.0 / 15.0, places=4)

    def test_editing_the_price_keeps_it_when_the_customer_discriminates_vat(self):
        line = self._create_line(self.res_partner_adhoc)

        with Form(line.order_id) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.price_unit_product_uom = 5.0

        self.assertAlmostEqual(line.price_unit, 75.0)

    def _create_line_in_tax_mode(self, partner, company_mode, order_mode, price_unit):
        """A line on an order whose tax mode differs from the one the company has by default."""
        self.company_ri.account_price_include = company_mode
        line = self._create_line(partner, price_unit=price_unit, document_tax_mode=order_mode)
        self.assertEqual(line.document_tax_mode, order_mode)
        return line

    def test_price_follows_the_tax_mode_of_the_order_when_the_customer_does_not_discriminate_vat(self):
        """A 1200 price with the VAT inside is 1200 for the customer, not 1452 as if it were a net price."""
        line = self._create_line_in_tax_mode(self.partner_cf, "tax_excluded", "tax_included", 1200.0)

        self.assertFalse(line.order_id.vat_discriminated)
        self.assertAlmostEqual(line._get_report_price_unit(), 1200.0, places=4)
        self.assertAlmostEqual(line.price_unit_product_uom, 1200.0 / 15.0, places=4)
        # The inverse the onchange of the product unit price uses
        self.assertAlmostEqual(line._get_price_unit_from_report_price(1200.0), 1200.0, places=4)

        line = self._create_line_in_tax_mode(self.partner_cf, "tax_included", "tax_excluded", 1000.0)

        self.assertAlmostEqual(line._get_report_price_unit(), 1210.0, places=4)
        self.assertAlmostEqual(line.price_unit_product_uom, 1210.0 / 15.0, places=4)
        self.assertAlmostEqual(line._get_price_unit_from_report_price(1210.0), 1000.0, places=4)

    def test_price_follows_the_tax_mode_of_the_order_when_the_customer_discriminates_vat(self):
        """A 1200 price with the VAT inside is 991.74 net for a customer that sees the VAT apart."""
        line = self._create_line_in_tax_mode(self.res_partner_adhoc, "tax_excluded", "tax_included", 1200.0)

        self.assertTrue(line.order_id.vat_discriminated)
        self.assertAlmostEqual(line._get_report_price_unit(), 1200.0 / 1.21, places=4)
        self.assertAlmostEqual(line.price_unit_product_uom, 1200.0 / 1.21 / 15.0, places=4)
        self.assertAlmostEqual(line._get_price_unit_from_report_price(1200.0 / 1.21), 1200.0, places=4)

        line = self._create_line_in_tax_mode(self.res_partner_adhoc, "tax_included", "tax_excluded", 1000.0)

        self.assertAlmostEqual(line._get_report_price_unit(), 1000.0, places=4)
        self.assertAlmostEqual(line.price_unit_product_uom, 1000.0 / 15.0, places=4)
        self.assertAlmostEqual(line._get_price_unit_from_report_price(1000.0), 1000.0, places=4)

    def test_changing_the_tax_mode_of_the_order_updates_the_price(self):
        line = self._create_line_in_tax_mode(self.partner_cf, "tax_excluded", "tax_excluded", 1000.0)
        self.assertAlmostEqual(line.price_unit_product_uom, 1210.0 / 15.0, places=4)

        line.order_id.document_tax_mode = "tax_included"

        self.assertAlmostEqual(line.price_unit_product_uom, 1000.0 / 15.0, places=4)
