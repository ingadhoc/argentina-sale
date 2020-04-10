from odoo import models, fields


class StockBook(models.Model):
    _inherit = 'stock.book'

    document_type_id = fields.Many2one(
        'l10n_latam.document.type',
        'Document Type',
    )
