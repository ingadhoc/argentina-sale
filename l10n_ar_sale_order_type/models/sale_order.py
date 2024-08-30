##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('type_id')
    def _compute_sale_checkbook(self):
        super()._compute_sale_checkbook()
        # si cambio a un type con checkbook siempre ponemos este
        # no lo pasamos a False si no tiene para respetar usos de False
        for order in self.filtered('type_id.sale_checkbook_id'):
            order.sale_checkbook_id = order.type_id.sale_checkbook_id
