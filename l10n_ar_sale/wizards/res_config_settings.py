from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_price_unit_with_tax = fields.Boolean(
        "Unit Price w/ Taxes",
        implied_group="l10n_ar_sale.sale_price_unit_with_tax",
    )
    group_delivery_date = fields.Boolean(
        "Show Delivery Date in Quotations report and online budget",
        implied_group="l10n_ar_sale.group_delivery_date_on_report_online",
    )
