from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_arba_cot_enabled = fields.Boolean(
        "Usar COT de ARBA?",
        help='Permite generar el COT de arba una vez que se han asignado '
        'números de remitos en las entregas',
        implied_group='l10n_ar_stock.arba_cot_enabled',
    )
    arba_cot = fields.Char(
        related='company_id.arba_cot',
        readonly=False,
    )
    cot_product_uom_qty = fields.Boolean(
        related='company_id.cot_product_uom_qty',
        readonly=False,
    )
