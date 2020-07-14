##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api


class ArbaCotWizard(models.TransientModel):
    _inherit = 'arba.cot.wizard'

    @api.model
    def default_get(self, default_fields):
        vals = super().default_get(default_fields)
        if self._context.get('active_model'):
            picking = self.env['stock.picking'].browse(self._context.get('active_id'))
            vals['partner_id'] = picking.carrier_id.partner_id.id
        return vals
