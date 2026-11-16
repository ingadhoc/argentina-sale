from lxml import etree
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBatchDeliveryGuide(TransactionCase):
    """A batch with contact gets a single delivery guide from our button; a batch without
    contact gets one per picking from the button of Odoo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.ar")
        cls.env.company.stock_move_email_validation = False
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito test lote",
                "sequence_code": "TESTBATGEN",
                "code": "outgoing",
                "company_id": cls.env.company.id,
                "warehouse_id": cls.env["stock.warehouse"]
                .search([("company_id", "=", cls.env.company.id)], limit=1)
                .id,
                "l10n_ar_document_type_id": cls.env.ref("l10n_ar.dc_remito_x").id,
                "l10n_ar_delivery_sequence_prefix": "00007",
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Producto lote test", "type": "consu"})
        cls.partner_a = cls.env["res.partner"].create({"name": "Cliente A lote test"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Cliente B lote test"})

    def _create_done_batch(self, partners, validate=True):
        pickings = self.env["stock.picking"].create(
            [
                {
                    "picking_type_id": self.picking_type.id,
                    "partner_id": partner.id,
                    "location_id": self.env.ref("stock.stock_location_stock").id,
                    "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                    "move_ids": [Command.create({"product_id": self.product.id, "product_uom_qty": 1.0})],
                }
                for partner in partners
            ]
        )
        batch = self.env["stock.picking.batch"].create(
            {
                "picking_type_id": self.picking_type.id,
                "company_id": self.env.company.id,
                "picking_ids": [Command.set(pickings.ids)],
            }
        )
        batch.action_confirm()
        if validate:
            pickings.button_validate()
            self.assertEqual(batch.state, "done")
        return batch, pickings

    def test_batch_with_contact_gets_a_single_delivery_guide(self):
        batch, pickings = self._create_done_batch([self.partner_a, self.partner_a])
        self.assertEqual(batch.partner_id, self.partner_a)
        batch.l10n_ar_action_create_delivery_guide()
        self.assertEqual([p.l10n_ar_delivery_guide_number for p in pickings], ["00007-00000001"] * 2)
        self.assertEqual(batch.l10n_ar_delivery_guide_number, "00007-00000001")

    def test_batch_without_contact_gets_one_delivery_guide_per_picking(self):
        batch, pickings = self._create_done_batch([self.partner_a, self.partner_b])
        self.assertFalse(batch.partner_id)
        batch.l10n_ar_action_create_delivery_guide()
        self.assertEqual(sorted(pickings.mapped("l10n_ar_delivery_guide_number")), ["00007-00000001", "00007-00000002"])

    def test_picking_list_action_in_batch_with_contact_gets_the_batch_delivery_guide(self):
        """The list action of the pickings must not give a delivery guide to each picking
        of a batch with contact."""
        batch, pickings = self._create_done_batch([self.partner_a, self.partner_a])
        other_batch, other_pickings = self._create_done_batch([self.partner_a, self.partner_b])
        (pickings | other_pickings).l10n_ar_action_create_delivery_guide()
        self.assertEqual([p.l10n_ar_delivery_guide_number for p in pickings], ["00007-00000001"] * 2)
        self.assertEqual(
            sorted(other_pickings.mapped("l10n_ar_delivery_guide_number")), ["00007-00000002", "00007-00000003"]
        )

    def test_auto_assign_gives_a_batch_with_contact_a_single_delivery_guide(self):
        self.picking_type.auto_assign_delivery_guide = True
        batch, pickings = self._create_done_batch([self.partner_a, self.partner_a, self.partner_a])
        self.assertEqual([p.l10n_ar_delivery_guide_number for p in pickings], ["00007-00000001"] * 3)
        self.assertEqual(batch.l10n_ar_delivery_guide_number, "00007-00000001")

    def test_auto_assign_in_batch_without_contact_gives_one_delivery_guide_per_picking(self):
        self.picking_type.auto_assign_delivery_guide = True
        batch, pickings = self._create_done_batch([self.partner_a, self.partner_b])
        self.assertEqual(sorted(pickings.mapped("l10n_ar_delivery_guide_number")), ["00007-00000001", "00007-00000002"])

    def test_picking_list_action_in_batch_with_contact_raises_when_it_cannot_generate(self):
        """Odoo raises for the transfers that cannot generate it, also inside a batch with contact."""
        draft_batch, draft_pickings = self._create_done_batch([self.partner_a, self.partner_a], validate=False)
        with self.assertRaisesRegex(UserError, "must be validated"):
            draft_pickings.l10n_ar_action_create_delivery_guide()
        batch, pickings = self._create_done_batch([self.partner_b, self.partner_b])
        batch.l10n_ar_action_create_delivery_guide()
        with self.assertRaisesRegex(UserError, "already have a delivery guide"):
            pickings.l10n_ar_action_create_delivery_guide()
        no_doc_batch, no_doc_pickings = self._create_done_batch([self.partner_a, self.partner_a])
        no_doc_batch.picking_type_id.l10n_ar_document_type_id = False
        with self.assertRaisesRegex(UserError, "not configured for delivery guides"):
            no_doc_pickings.l10n_ar_action_create_delivery_guide()

    def test_batch_list_action_skips_batches_that_cannot_generate(self):
        draft_batch, draft_pickings = self._create_done_batch([self.partner_a, self.partner_a], validate=False)
        batch, pickings = self._create_done_batch([self.partner_b, self.partner_b])
        (draft_batch | batch).l10n_ar_action_create_delivery_guide()
        self.assertFalse(any(draft_pickings.mapped("l10n_ar_delivery_guide_number")))
        self.assertEqual(batch.l10n_ar_delivery_guide_number, "00007-00000001")

    def test_one_generate_button_per_case(self):
        """Our button needs a contact on the batch, and the button of Odoo is hidden then."""
        arch = etree.fromstring(self.env["stock.picking.batch"].get_view(view_type="form")["arch"])
        buttons = {
            button.get("string"): button.get("invisible")
            for button in arch.xpath("//header//button[@name='l10n_ar_action_create_delivery_guide']")
        }
        self.assertIn("not partner_id", buttons["Generate Delivery Guide"])
        self.assertIn("or partner_id", buttons["Generate Delivery Guides"])
