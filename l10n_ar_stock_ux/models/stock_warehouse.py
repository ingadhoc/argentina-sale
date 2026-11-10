from odoo import models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    def write(self, vals):
        # Archiving the warehouse or changing its steps or code rewrites its operation types:
        # legacy delivery guide data of those types must not block it.
        return super(StockWarehouse, self.with_context(l10n_ar_skip_legacy_checks=True)).write(vals)
