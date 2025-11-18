from odoo import fields, models


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
