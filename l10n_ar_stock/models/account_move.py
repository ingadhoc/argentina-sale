from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_invoiced_lot_values(self):
        lot_values = super()._get_invoiced_lot_values()
        for lot_val in lot_values:
            lot = self.env['stock.production.lot'].browse(lot_val['lot_id'])
            lot_val['dispatch_number'] = lot.dispatch_number
        return lot_values
