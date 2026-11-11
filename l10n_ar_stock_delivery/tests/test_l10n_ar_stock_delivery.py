from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install_l10n", "post_install", "-at_install")
class TestL10nArStockDelivery(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.ar")
        # Carrier partner with CUIT and address, as the delivery slip prints them
        cls.carrier_partner = cls.env["res.partner"].create(
            {
                "name": "Transportes Test",
                "is_company": True,
                "country_id": cls.env.ref("base.ar").id,
                "l10n_latam_identification_type_id": cls.env.ref("l10n_ar.it_cuit").id,
                "vat": "30714295698",
                "street": "Calle Transporte 123",
                "city": "Rosario",
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier test",
                "delivery_type": "fixed",
                "product_id": cls.env["product.product"].create({"name": "Envío test", "type": "service"}).id,
                "partner_id": cls.carrier_partner.id,
            }
        )
        product = cls.env["product.product"].create({"name": "Producto con peso", "type": "consu", "weight": 2.5})
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "partner_id": cls.env["res.partner"].create({"name": "Cliente test"}).id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "carrier_id": cls.carrier.id,
                "carrier_tracking_ref": "TRACK-0001",
                "move_ids": [(0, 0, {"product_id": product.id, "product_uom_qty": 2.0})],
            }
        )

    def test_delivery_slip_prints_weight_tracking_and_carrier(self):
        """The AR delivery slip adds the weight, the tracking number and the carrier
        with its identification and address."""
        # The weight comes from the moves: 2 units of 2.5
        self.assertEqual(self.picking.weight, 5.0)
        html = self.env["ir.actions.report"]._render_qweb_html("stock.action_report_delivery", self.picking.ids)[0]
        html = html.decode()
        for label, expected in (
            ("weight", "Weight:"),
            ("tracking number", "TRACK-0001"),
            ("carrier name", "Carrier test"),
            ("carrier identification", "30714295698"),
            ("carrier address", "Calle Transporte 123"),
        ):
            with self.subTest(label):
                # Compare this way to avoid dumping the whole HTML on failure
                self.assertTrue(expected in html, f"the delivery slip has to print the {label} ({expected})")

    def test_arba_cot_wizard_defaults_to_carrier_partner(self):
        """Opening the ARBA COT wizard from a picking fills in the picking's carrier."""
        wizard_model = self.env["arba.cot.wizard"].with_context(
            active_model="stock.picking", active_id=self.picking.id, active_ids=self.picking.ids
        )
        defaults = wizard_model.default_get(["partner_id"])
        self.assertEqual(defaults.get("partner_id"), self.carrier_partner.id)
