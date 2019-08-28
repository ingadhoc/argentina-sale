from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_allow_vat_no_discrimination = fields.Selection(
        related='company_id.sale_allow_vat_no_discrimination',
        readonly=False,
    )
    group_price_unit_with_tax = fields.Boolean(
        "Unit Price w/ Taxes",
        implied_group='l10n_ar_sale.sale_price_unit_with_tax',
    )
    group_use_sale_checkbook = fields.Boolean(
        "Use Sale Checkbook in Sales",
        implied_group='l10n_ar_sale.use_sale_checkbook',
    )
