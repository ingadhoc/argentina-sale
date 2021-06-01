from odoo import models, fields


class StockBook(models.Model):
    _inherit = 'stock.book'

    document_type_id = fields.Many2one(
        'l10n_latam.document.type',
        'Document Type',
    )
    # TODO when CAE addded by afip for remitos, we should add a selector
    # so that we can use with autoimpresores and electronic remitos
    l10n_ar_cai = fields.Char(
        'CAI',
        help='Solo complete este dato si es auto-impresor',
    )
    l10n_ar_cai_due = fields.Date(
        'Vencimiento CAI',
        help='Solo complete este dato si es auto-impresor',
    )
    report_partner_id = fields.Many2one(
        'res.partner',
        string='Contacto para Encabezado',
        help='Para el encabezado de los remitos/comprobantes de entrega, la información a utilizar se obtendrá del '
        'primer datos definido de estos lugares:\n'
        '* Este campo\n'
        '* Dirección del Almacen de la transferencia\n'
        '* Información de la compañía de la transferencia'
    )
    report_signature_section = fields.Boolean(
        string="Añadir sección firma",
        help="Agregar al reporte una sección para añadir firma de confirmación de recepción.",
        default=False,
    )
