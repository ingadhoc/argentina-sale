from odoo import _, models
from odoo.exceptions import UserError

# El paperformat del tipo de operación viaja por contexto entre el render y get_paperformat().
PREPRINTED_PAPERFORMAT_CONTEXT_KEY = "l10n_ar_preprinted_paperformat_id"


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        """Acá es donde todavía sabemos qué transferencias se están imprimiendo, así que es acá
        donde resolvemos el paperformat del tipo de operación y lo dejamos en el contexto para
        que ``get_paperformat`` lo encuentre.

        El dato no puede resolverse más adelante: ``get_paperformat`` es un método de
        ``ir.actions.report`` y el motor lo llama sin los registros ni nada que los identifique
        (el contexto que llega trae lang, tz y uid, nada más). El mismo patrón usa ``l10n_ch``
        para el formato de las cartas de snailmail.

        Entra por este método y no por ``_render_qweb_pdf`` porque este es el que el motor usa
        siempre: lo atraviesan la impresión desde el botón, el adjunto y también el render con
        el que ``l10n_ar_stock_preprinted`` cuenta las hojas antes de numerar. Que el conteo use
        la misma geometría que la impresión no es un efecto colateral, es un requisito: si
        contara con otra, los números del talonario no coincidirían con las hojas que salen."""
        report = self._get_report(report_ref)
        paperformat = report._l10n_ar_preprinted_paperformat(res_ids)
        record = self
        if paperformat:
            record = self.with_context(**{PREPRINTED_PAPERFORMAT_CONTEXT_KEY: paperformat.id})
        return super(IrActionsReport, record)._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)

    def get_paperformat(self):
        """El paperformat del tipo de operación gana sobre el del reporte y el de la compañía."""
        paperformat_id = self.env.context.get(PREPRINTED_PAPERFORMAT_CONTEXT_KEY)
        if paperformat_id:
            return self.env["report.paperformat"].browse(paperformat_id)
        return super().get_paperformat()

    def _l10n_ar_preprinted_paperformat(self, res_ids):
        """El paperformat propio de las transferencias que se están imprimiendo, si lo tienen.

        Devuelve vacío —y entonces manda el paperformat del reporte, como siempre— cuando el
        reporte no es el remito, cuando no hay transferencias, o cuando ninguna está en
        preimpreso con paperformat propio.

        Una tanda que mezcla geometrías no se puede imprimir de una: wkhtmltopdf recibe un solo
        juego de medidas por corrida, así que el PDF saldría con la geometría de unas y no de
        otras. En papel preimpreso eso no es un PDF feo, es papel numerado arruinado, así que
        avisamos y que se impriman por separado."""
        self.ensure_one()
        if not res_ids or self != self.env.ref("stock.action_report_delivery", raise_if_not_found=False):
            return self.env["report.paperformat"]
        pickings = self.env["stock.picking"].browse(res_ids).exists()
        paperformats = {picking._l10n_ar_preprinted_paperformat() for picking in pickings}
        if not any(paperformats):
            return self.env["report.paperformat"]
        if len(paperformats) > 1:
            raise UserError(
                _(
                    "Está imprimiendo juntas transferencias con formatos de papel distintos"
                    " (%(picking_types)s), y el remito se imprime con uno solo por vez.\n"
                    "Imprima por separado las de cada tipo de operación.",
                    picking_types=", ".join(sorted(set(pickings.picking_type_id.mapped("display_name")))),
                )
            )
        return paperformats.pop()
