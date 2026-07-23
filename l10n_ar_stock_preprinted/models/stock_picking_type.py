from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_ar_is_preprinted = fields.Boolean(
        string="Remito Preimpreso",
        compute="_compute_l10n_ar_is_preprinted",
        help="Argentina: se considera 'preimpreso' cuando el tipo de operación tiene un tipo de "
        "documento de remito configurado pero NO tiene CAI cargado. En ese caso el papel del remito "
        "viene preimpreso de imprenta, ya con su numeración y CAI; Odoo solo imprime el contenido "
        "variable (sin encabezado, sin CAI y sin número). Si el CAI está cargado se trata de un "
        "remito autoimpreso y se imprime el comprobante completo.",
    )
    l10n_ar_lines_per_voucher = fields.Integer(
        string="Renglones por Remito",
        help="Argentina (preimpreso): cantidad de renglones que entran en cada hoja/comprobante "
        "preimpreso. Se usa para calcular cuántos números de remito consume una entrega larga "
        "(cada hoja preimpresa tiene su propio número). Si se deja en 0, cada entrega consume un "
        "único número.",
    )

    @api.depends("l10n_ar_document_type_id", "l10n_ar_cai_authorization_code")
    def _compute_l10n_ar_is_preprinted(self):
        for rec in self:
            rec.l10n_ar_is_preprinted = bool(rec.l10n_ar_document_type_id) and not rec.l10n_ar_cai_authorization_code
