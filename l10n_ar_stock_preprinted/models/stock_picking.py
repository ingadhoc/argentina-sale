from io import BytesIO

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_ar_is_preprinted = fields.Boolean(
        related="picking_type_id.l10n_ar_is_preprinted",
    )

    def _l10n_ar_count_preprinted_sheets(self):
        """Cantidad de hojas que consume el remito preimpreso = cantidad de páginas que
        realmente se imprimen con productos. Se obtiene renderizando el comprobante de
        entrega y contando las páginas del PDF resultante."""
        self.ensure_one()
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            from pypdf import PdfReader
        report = self.env.ref("stock.action_report_delivery")
        pdf_content, _dummy = report.sudo()._render_qweb_pdf(report.id, self.ids)
        return max(1, len(PdfReader(BytesIO(pdf_content)).pages))

    def l10n_ar_action_create_delivery_guide(self):
        """En remitos preimpresos numeramos según las hojas realmente impresas (una por
        página del comprobante), con varios números separados por coma y sin datos de CAI
        (el CAI viene preimpreso en el papel). En autoimpresos se delega al flujo estándar
        de Odoo (un número + datos de CAI)."""
        self.ensure_one()
        if self.l10n_ar_is_preprinted:
            if not self.l10n_ar_delivery_guide_number:
                picking_type = self.picking_type_id
                picking_type._ensure_l10n_ar_stock_sequence()
                sheets = self._l10n_ar_count_preprinted_sheets()
                numbers = [picking_type.l10n_ar_sequence_id.next_by_id() for __ in range(sheets)]
                self.l10n_ar_delivery_guide_number = ",".join(numbers)
                # el CAI no aplica al preimpreso (viene impreso en el papel)
                self.l10n_ar_cai_data = {
                    "document_type_id": picking_type.l10n_ar_document_type_id.id,
                }
            return
        return super().l10n_ar_action_create_delivery_guide()
