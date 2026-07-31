import re
from io import BytesIO

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_ar_voucher_print_mode = fields.Selection(
        related="picking_type_id.l10n_ar_voucher_print_mode",
    )

    def _l10n_ar_count_pages_with_products(self, pdf_reader):
        """Cuenta las páginas del PDF que realmente contienen líneas de producto,
        analizando el texto de cada hoja: una hoja que solo trae firma o totales NO
        consume número de remito. La detección usa los identificadores del producto
        (código interno / código de barras) para ser independiente del idioma; si el
        producto no tiene código, cae a un patrón numérico genérico (cantidad/precio
        con decimales)."""
        self.ensure_one()
        move_lines = self.move_line_ids or self.move_ids
        identifiers = set()
        for line in move_lines:
            product = line.product_id
            if product.default_code:
                identifiers.add(product.default_code.lower().strip())
            if product.barcode:
                identifiers.add(product.barcode.lower().strip())

        pages_with_products = 0
        for page in pdf_reader.pages:
            try:
                text = (page.extract_text() or "").lower()
            except Exception:
                # Si no se puede extraer el texto, asumimos que la hoja trae productos.
                pages_with_products += 1
                continue
            if not text:
                continue
            if identifiers:
                has_products = any(identifier in text for identifier in identifiers)
            else:
                has_products = bool(re.search(r"\b\d+[.,]\d+\b", text))
            if has_products:
                pages_with_products += 1
        return max(1, pages_with_products)

    def _l10n_ar_count_preprinted_sheets(self):
        """Cantidad de hojas que consume el remito preimpreso = cantidad de páginas que
        realmente se imprimen con productos (las hojas de solo firma/totales no consumen
        número). Se obtiene renderizando el comprobante de entrega y contando esas páginas
        del PDF resultante."""
        self.ensure_one()
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            from pypdf import PdfReader
        report = self.env.ref("stock.action_report_delivery")
        pdf_content, _dummy = report.sudo()._render_qweb_pdf(report.id, self.ids)
        return self._l10n_ar_count_pages_with_products(PdfReader(BytesIO(pdf_content)))

    def l10n_ar_action_create_delivery_guide(self):
        """En remitos preimpresos numeramos según las hojas realmente impresas (una por
        página del comprobante), con varios números separados por coma y sin datos de CAI
        (el CAI viene preimpreso en el papel), y devolvemos la acción de impresión: el
        botón numera e imprime en un solo paso. Los números NO se imprimen en el PDF (el
        papel de imprenta ya los trae); solo se registran en el picking. Cuando el método
        corre desde ``_action_done`` (autoasignación) el retorno se ignora, así que no
        dispara impresiones automáticas. En autoimpresos se delega al flujo estándar de
        Odoo (un número + datos de CAI)."""
        self.ensure_one()
        if self.l10n_ar_voucher_print_mode == "preprinted":
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
            return self.env.ref("stock.action_report_delivery").report_action(self)
        return super().l10n_ar_action_create_delivery_guide()
