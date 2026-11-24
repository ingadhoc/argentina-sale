from io import BytesIO

from odoo import fields, models
from odoo.tools.pdf import PdfReader


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    l10n_ar_voucher_print_mode = fields.Selection(related="picking_type_id.l10n_ar_voucher_print_mode")

    def _l10n_ar_count_preprinted_sheets(self):
        """Sheets the batch voucher uses: the pages of its report, counting a single copy.

        Same count as StockPicking._l10n_ar_count_preprinted_sheets, but over the batch
        report, which lists the products of all the transfers of the batch.
        """
        self.ensure_one()
        # sudo and l10n_ar_counting for the same reasons as in the picking count
        report = self.env.ref("stock_batch_picking_ux.action_report_batch_deliveryslip")
        report = report.sudo().with_context(l10n_ar_counting=True)
        pdf_content, _dummy = report._render_qweb_pdf(report.id, self.ids)
        pages = len(PdfReader(BytesIO(pdf_content)).pages)
        return max(1, pages // len(self._l10n_ar_get_copies_list()))
