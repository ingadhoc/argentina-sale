from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_ar_autoprinted = fields.Boolean(
        string="Autoimpreso",
        compute="_compute_l10n_ar_preprinted_flags",
        help="Argentina: se autocalcula según el CAI. Con CAI cargado el remito es autoimpreso "
        "(Odoo imprime el comprobante completo: encabezado, número y CAI). Sin CAI es preimpreso "
        "(el papel de imprenta ya trae encabezado, numeración y CAI; Odoo solo imprime el contenido "
        "variable y numera según las hojas que se imprimen).",
    )
    l10n_ar_is_preprinted = fields.Boolean(
        string="Remito Preimpreso",
        compute="_compute_l10n_ar_preprinted_flags",
        help="Argentina: verdadero cuando el tipo de operación tiene un tipo de documento de remito "
        "configurado y NO tiene CAI (es preimpreso). Lo usan el reporte y la numeración.",
    )

    @api.depends("l10n_ar_document_type_id", "l10n_ar_cai_authorization_code")
    def _compute_l10n_ar_preprinted_flags(self):
        for rec in self:
            has_doc_type = bool(rec.l10n_ar_document_type_id)
            has_cai = bool(rec.l10n_ar_cai_authorization_code)
            rec.l10n_ar_autoprinted = has_doc_type and has_cai
            rec.l10n_ar_is_preprinted = has_doc_type and not has_cai
