from odoo import models, fields


class StockBook(models.Model):
    _inherit = 'stock.book'

    document_type_id = fields.Many2one(
        'l10n_latam.document.type',
        'Document Type',
    )
    l10n_ar_cai = fields.Char(
        'CAI',
        help='Solo complete este dato si es auto-impresor',
    )
    l10n_ar_cai_due = fields.Date(
        'Vencimiento CAI',
        help='Solo complete este dato si es auto-impresor',
    )
