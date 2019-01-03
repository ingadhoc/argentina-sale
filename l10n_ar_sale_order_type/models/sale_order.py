##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('company_id', 'type_id')
    def set_sale_checkbook(self):
        if self.type_id.sale_checkbook_id:
            self.sale_checkbook_id = self.type_id.sale_checkbook_id
        else:
            return super(SaleOrder, self).set_sale_checkbook()
