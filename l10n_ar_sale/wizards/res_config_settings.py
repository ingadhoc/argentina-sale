from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_price_unit_with_tax = fields.Boolean(
        "Unit Price w/ Taxes",
        implied_group='l10n_ar_sale.sale_price_unit_with_tax',
    )
    group_use_sale_checkbook = fields.Boolean(
        "Use Sale Checkbook in Sales",
        implied_group='l10n_ar_sale.use_sale_checkbook',
    )
