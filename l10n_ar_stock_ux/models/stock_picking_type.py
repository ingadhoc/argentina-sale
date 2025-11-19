from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    report_partner_id = fields.Many2one(
        "res.partner",
        string="Contacto para Encabezado",
        help="Para el encabezado de los remitos/comprobantes de entrega, la información a utilizar se obtendrá del "
        "primer datos definido de estos lugares:\n"
        "* Este campo\n"
        "* Dirección del Almacen de la transferencia\n"
        "* Información de la compañía de la transferencia",
    )
    report_signature_section = fields.Boolean(
        string="Añadir sección firma",
        help="Agregar al reporte una sección para añadir firma de confirmación de recepción.",
        default=False,
    )
    auto_assign_delivery_guide = fields.Boolean(
        string="Auto Assign Delivery Guide Number",
        help="Al validar una transferencia de este tipo, se asignará automáticamente un número de remito.",
        default=False,
    )

    @api.onchange("l10n_ar_sequence_number_start")
    def _add_padding_to_sequence_number_start(self):
        if self.l10n_ar_sequence_number_start:
            self.l10n_ar_sequence_number_start = self.l10n_ar_sequence_number_start.zfill(8)

    @api.onchange("l10n_ar_sequence_number_end")
    def _add_padding_to_sequence_number_end(self):
        if self.l10n_ar_sequence_number_end:
            self.l10n_ar_sequence_number_end = self.l10n_ar_sequence_number_end.zfill(8)
