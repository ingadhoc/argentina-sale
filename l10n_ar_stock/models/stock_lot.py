##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    dispatch_number = fields.Char(
    )
