##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('type_id')
    def _onchange_sale_checkbook_id(self):
        if self.type_id and self.type_id.sale_checkbook_id:
            self.sale_checkbook_id = self.type_id.sale_checkbook_id
