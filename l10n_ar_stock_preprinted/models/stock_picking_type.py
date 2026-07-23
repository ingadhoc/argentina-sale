from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_ar_autoprinted = fields.Boolean(
        string="Autoimpreso",
        default=True,
        help="Argentina: si está tildado, el remito es autoimpreso: Odoo imprime el comprobante "
        "completo (encabezado, número y CAI) y por eso el CAI es obligatorio. Si se destilda, el "
        "remito es preimpreso (el papel de imprenta ya trae encabezado, numeración y CAI): no se "
        "pide CAI y Odoo solo imprime el contenido variable, numerando según las hojas consumidas.",
    )
    l10n_ar_is_preprinted = fields.Boolean(
        string="Remito Preimpreso",
        compute="_compute_l10n_ar_is_preprinted",
        help="Argentina: verdadero cuando el tipo de operación tiene un tipo de documento de remito "
        "configurado y NO es autoimpreso. Lo usa el reporte y la numeración.",
    )
    l10n_ar_lines_per_voucher = fields.Integer(
        string="Renglones por Remito",
        help="Argentina (preimpreso): cantidad de renglones que entran en cada hoja/comprobante "
        "preimpreso. Se usa para calcular cuántos números de remito consume una entrega larga "
        "(cada hoja preimpresa tiene su propio número). Si se deja en 0, cada entrega consume un "
        "único número.",
    )

    @api.depends("l10n_ar_document_type_id", "l10n_ar_autoprinted")
    def _compute_l10n_ar_is_preprinted(self):
        for rec in self:
            rec.l10n_ar_is_preprinted = bool(rec.l10n_ar_document_type_id) and not rec.l10n_ar_autoprinted
