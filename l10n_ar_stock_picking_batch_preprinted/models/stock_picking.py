from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _l10n_ar_count_preprinted_sheets(self):
        # The voucher of a batch with partner is the batch one, so the sheets are the ones of
        # its report, not the ones of this transfer alone.
        self.ensure_one()
        if self.batch_partner_id:
            return self.batch_id._l10n_ar_count_preprinted_sheets()
        return super()._l10n_ar_count_preprinted_sheets()
