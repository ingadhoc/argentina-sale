from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_ar_autoprinted = fields.Boolean(
        string="Autoimpreso",
        default=True,
        help="Argentina: cuando está activo el remito es autoimpreso (Odoo imprime el comprobante "
        "completo: encabezado, número y CAI, y el CAI con su vencimiento son obligatorios). Cuando se "
        "desactiva el remito es preimpreso: el papel de imprenta ya trae encabezado, numeración y CAI, "
        "por lo que el CAI deja de pedirse y Odoo solo imprime el contenido variable numerando según "
        "las hojas que se consumen.",
    )
    l10n_ar_is_preprinted = fields.Boolean(
        string="Remito Preimpreso",
        compute="_compute_l10n_ar_is_preprinted",
        help="Argentina: verdadero cuando el tipo de operación tiene un tipo de documento de remito "
        "configurado y NO es autoimpreso (es preimpreso). Lo usan el reporte y la numeración.",
    )

    @api.depends("l10n_ar_document_type_id", "l10n_ar_autoprinted")
    def _compute_l10n_ar_is_preprinted(self):
        for rec in self:
            rec.l10n_ar_is_preprinted = bool(rec.l10n_ar_document_type_id) and not rec.l10n_ar_autoprinted
