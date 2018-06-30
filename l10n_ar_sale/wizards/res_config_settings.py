from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_allow_vat_no_discrimination = fields.Selection(
        related='company_id.sale_allow_vat_no_discrimination'
    )
    group_price_unit_with_tax = fields.Boolean(
        "Show Unit Price w/ Taxes On sale Order Lines",
        implied_group='l10n_ar_sale.sale_price_unit_with_tax',
    )
