##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class SaleOrderType(models.Model):
    _inherit = "sale.order.type"

    sale_checkbook_id = fields.Many2one(
        'sale.checkbook',
        check_company=True,
    )
