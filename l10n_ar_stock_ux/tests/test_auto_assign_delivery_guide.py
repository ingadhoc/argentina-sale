from unittest.mock import patch

from odoo import Command
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.addons.l10n_ar_stock.models.stock_picking import StockPicking as L10nArStockPicking
from odoo.addons.stock.models.stock_picking import StockPicking as StockStockPicking
from odoo.tests import tagged


@tagged("post_install_l10n", "post_install", "-at_install")
class TestAutoAssignDeliveryGuide(TestArCommon):
    """Ticket #125173: la asignación automática del nro de remito consume una secuencia
    no_gap (lock de fila sobre ir_sequence hasta el commit), por lo que debe hacerse al
    final de la validación — con el picking ya en done — y no antes de _action_done.
    Cuando la compañía envía el mail de confirmación, el nro debe estar asignado al
    momento del envío para que el reporte adjunto salga con el nro argentino."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wh = cls.env["stock.warehouse"].search([("company_id", "=", cls.company_ri.id)], limit=1)
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito Outgoing Auto",
                "code": "outgoing",
                "company_id": cls.company_ri.id,
                "sequence_code": "OUTAUTO",
                "auto_assign_delivery_guide": True,
                "l10n_ar_document_type_id": cls.env.ref("l10n_ar.dc_r_r").id,
                "l10n_ar_cai_authorization_code": "99999999999999",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "99999999",
            }
        )

    def _create_picking(self):
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.wh.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "picking_type_id": self.picking_type.id,
                "partner_id": self.partner_ri.id,
                "move_ids": [Command.create({"product_id": self.product.id, "product_uom_qty": 1.0})],
            }
        )
        picking.action_confirm()
        return picking

    def _validate_recording_states(self, picking):
        """Valida el picking espiando en qué estado estaba al asignársele el nro de remito."""
        states = []
        original = L10nArStockPicking.l10n_ar_action_create_delivery_guide

        def _spy(record):
            states.append(record.state)
            return original(record)

        with patch.object(L10nArStockPicking, "l10n_ar_action_create_delivery_guide", _spy):
            picking.button_validate()
        return states

    def test_assign_after_done_without_confirmation_email(self):
        """Sin mail de confirmación el nro se asigna con el picking ya validado,
        minimizando la ventana del lock de la secuencia no_gap."""
        self.company_ri.stock_move_email_validation = False
        picking = self._create_picking()
        states = self._validate_recording_states(picking)
        self.assertTrue(picking.l10n_ar_delivery_guide_number, "El nro de remito debe asignarse igual.")
        self.assertEqual(states, ["done"], "El nro debe asignarse al final de la validación, no antes.")

    def test_number_available_when_confirmation_email_is_sent(self):
        """Con mail de confirmación activo, el nro ya debe estar asignado al momento del
        envío (el reporte que adjunta el mail lo embebe), sin adelantar la asignación al
        inicio de la validación."""
        self.company_ri.stock_move_email_validation = True
        picking = self._create_picking()
        numbers_at_send = []

        # espiamos el hook nativo (el super() de nuestro override): registra qué nro
        # tenía el picking al momento del envío y neutraliza el envío real, que es
        # comportamiento de stock y no lo que se prueba acá
        def _spy_send(record):
            numbers_at_send.extend(record.mapped("l10n_ar_delivery_guide_number"))

        with patch.object(StockStockPicking, "_send_confirmation_email", _spy_send):
            states = self._validate_recording_states(picking)

        self.assertTrue(picking.l10n_ar_delivery_guide_number, "El nro de remito debe asignarse igual.")
        self.assertEqual(states, ["done"], "El nro debe asignarse al final de la validación, no antes.")
        self.assertEqual(
            numbers_at_send,
            [picking.l10n_ar_delivery_guide_number],
            "El nro ya debe estar asignado cuando se envía el mail de confirmación.",
        )
