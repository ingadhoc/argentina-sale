from unittest.mock import patch

from odoo import Command, fields
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged


@tagged("post_install_l10n", "post_install", "-at_install")
class TestDeliveryGuidePrefix(TestArCommon):
    """The delivery guide prefix is required, and prefixes that cannot be used to emit fail
    with a clear error before numbering or building the COT."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.company_ri.id)], limit=1)
        cls.product = cls.env["product.product"].create({"name": "Producto prefijo test", "type": "consu"})

    def _create_picking_type(self, sequence_code, document_type, prefix):
        vals = {
            "name": f"Remito {sequence_code}",
            "code": "outgoing",
            "company_id": self.company_ri.id,
            "warehouse_id": self.warehouse.id,
            "sequence_code": sequence_code,
            "l10n_ar_document_type_id": document_type.id,
            "l10n_ar_delivery_sequence_prefix": prefix,
        }
        if document_type == self.env.ref("l10n_ar.dc_r_r"):
            vals.update(
                {
                    "l10n_ar_cai_authorization_code": "12345678901234",
                    "l10n_ar_cai_expiration_date": "2030-12-31",
                    "l10n_ar_sequence_number_start": "00000001",
                    "l10n_ar_sequence_number_end": "99999999",
                }
            )
        return self.env["stock.picking.type"].create(vals)

    def _create_picking(self, picking_type):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": self.partner_ri.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [Command.create({"product_id": self.product.id, "product_uom_qty": 1.0})],
            }
        )

    def test_prefix_is_required_and_up_to_5_characters(self):
        picking_type = self._create_picking_type("PRE-REQ", self.env.ref("l10n_ar.dc_r_r"), "00001")
        with self.assertRaises(ValidationError):
            picking_type.l10n_ar_delivery_sequence_prefix = False
        with self.assertRaises(ValidationError):
            picking_type.l10n_ar_delivery_sequence_prefix = "000001"
        # letters are still accepted when configuring
        picking_type.l10n_ar_delivery_sequence_prefix = "000X"
        self.assertEqual(picking_type.l10n_ar_delivery_sequence_prefix, "000X")

    def test_document_type_without_prefix_cannot_be_saved(self):
        """Without a document type no sequence is created, so setting only the document type
        later leaves the type without prefix."""
        picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Remito sin prefijo",
                "code": "outgoing",
                "company_id": self.company_ri.id,
                "sequence_code": "PRE-NODOC",
            }
        )
        with self.assertRaises(ValidationError):
            picking_type.l10n_ar_document_type_id = self.env.ref("l10n_ar.dc_remito_x")

    def test_legacy_type_without_prefix(self):
        """A type that lost its prefix cannot be saved until it gets one, and emitting fails
        with a clear error instead of the SQL one."""
        picking_type = self._create_picking_type("PRE-OLD", self.env.ref("l10n_ar.dc_r_r"), "00001")
        picking_type.l10n_ar_sequence_id.prefix = False
        picking_type.invalidate_recordset(["l10n_ar_delivery_sequence_prefix"])
        picking = self._create_picking(picking_type)

        with self.assertRaisesRegex(UserError, "has no delivery guide prefix"):
            picking.l10n_ar_action_create_delivery_guide()
        self.assertFalse(picking.l10n_ar_delivery_guide_number)
        with self.assertRaisesRegex(ValidationError, "needs a delivery guide prefix"):
            picking_type.name = "Remito renombrado"
        # module install and upgrade writes do not abort on it
        with patch.object(self.env.registry, "ready", False):
            picking_type.name = "Remito renombrado en upgrade"
        picking_type.write({"name": "Remito renombrado", "l10n_ar_delivery_sequence_prefix": "00002"})
        picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(picking.l10n_ar_delivery_guide_number, "00002-00000001")

    def test_autoprinted_remito_r_with_letters_does_not_take_a_number(self):
        picking_type = self._create_picking_type("PRE-R-X", self.env.ref("l10n_ar.dc_r_r"), "000X")
        sequence = picking_type.l10n_ar_sequence_id
        next_number = sequence.number_next_actual
        picking = self._create_picking(picking_type)

        with self.assertRaisesRegex(UserError, "only accepts numbers"):
            picking.l10n_ar_action_create_delivery_guide()
        self.assertFalse(picking.l10n_ar_delivery_guide_number)
        sequence.invalidate_recordset(["number_next_actual"])
        self.assertEqual(sequence.number_next_actual, next_number)

    def test_remito_x_accepts_letters_in_prefix(self):
        picking_type = self._create_picking_type("PRE-X-X", self.env.ref("l10n_ar.dc_remito_x"), "000X")
        picking = self._create_picking(picking_type)
        picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(picking.l10n_ar_delivery_guide_number, "000X-00000001")

    def test_cot_rejects_prefix_with_letters(self):
        picking_type = self._create_picking_type("PRE-COT", self.env.ref("l10n_ar.dc_remito_x"), "000X")
        picking = self._create_picking(picking_type)
        picking.l10n_ar_action_create_delivery_guide()

        with self.assertRaisesRegex(UserError, "000X-00000001"):
            picking._get_arba_file_data(fields.Datetime.now(), "U", self.partner_ri, False, False, "0", 0.0)
