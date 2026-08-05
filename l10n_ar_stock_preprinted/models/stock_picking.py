from io import BytesIO

from odoo import fields, models
from odoo.tools.pdf import PdfReader

# copias que agrega el reporte según ir.actions.report.l10n_ar_copies (l10n_ar_ux):
# cada copia repite TODAS las páginas del comprobante
COPIES_BY_L10N_AR_COPIES = {"duplicado": 2, "triplicado": 3}

# marca invisible (texto blanco de 1px) que el comprobante imprime una vez por línea de
# producto cuando se renderiza para contar hojas (contexto l10n_ar_counting). Permite saber
# qué páginas tienen productos sin depender de que el producto tenga código ni de heurísticas
# de texto: una hoja de solo transportista / firma / totales no la lleva y no consume número.
L10N_AR_PREPRINTED_LINE_MARK = "PREPRINTEDLINEMARK"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_ar_voucher_print_mode = fields.Selection(
        related="picking_type_id.l10n_ar_voucher_print_mode",
    )

    def _l10n_ar_count_pages_with_products(self, pages):
        """Cuenta cuántas de ``pages`` contienen líneas de producto: una hoja que solo trae
        firma, totales o datos del transportista NO consume número de remito. El comprobante
        imprime una marca invisible (``L10N_AR_PREPRINTED_LINE_MARK``) por cada línea de
        producto cuando se renderiza con el contexto de conteo, así que una página con
        productos trae al menos una marca. Es independiente del idioma y de que el producto
        tenga código interno o de barras.

        Recibe las páginas y no el PdfReader completo porque el PDF trae el comprobante
        repetido una vez por copia: hay que contar sobre UNA sola copia (ver
        ``_l10n_ar_count_preprinted_sheets``)."""
        self.ensure_one()
        pages_with_products = 0
        for page in pages:
            try:
                text = page.extract_text() or ""
            except Exception:
                # Si no se puede extraer el texto, asumimos que la hoja trae productos.
                pages_with_products += 1
                continue
            if L10N_AR_PREPRINTED_LINE_MARK in text:
                pages_with_products += 1
        return max(1, pages_with_products)

    def _l10n_ar_count_preprinted_sheets(self):
        """Cantidad de hojas que consume el remito preimpreso = cantidad de páginas que
        realmente se imprimen con productos (las hojas de solo firma/totales no consumen
        número). Se obtiene renderizando el comprobante de entrega y contando esas páginas
        del PDF resultante. El render es el mismo comprobante argentino que se imprime
        (``l10n_ar_stock_ux`` lo elige para toda transferencia de compañía AR), así que la
        paginación que contamos es la que sale en papel.

        El PDF trae el comprobante repetido tantas veces como copias tenga configurado el
        reporte (original / duplicado / triplicado), y el juego de copias consume UN solo
        número por hoja, así que contamos únicamente sobre las páginas de la primera copia."""
        self.ensure_one()
        report = self.env.ref("stock.action_report_delivery")
        # Renderizamos con sudo y con el contexto l10n_ar_counting:
        # - sudo: numerar no puede depender de los permisos de lectura del que valida. Quien
        #   dispara el conteo (al validar, si el tipo de operación autoasigna) no es
        #   necesariamente quien después imprime, y el comprobante toca modelos relacionados
        #   que un operador de depósito puede no tener permitido leer. Ojo: el motor de
        #   reportes NO eleva por su cuenta (ver _render_qweb_pdf_prepare_streams, "evaluation
        #   context as current user"), así que si el comprobante necesita sudo para renderizar
        #   eso es un problema del template, no algo que este método deba tapar.
        # - l10n_ar_counting: el conteo corre ANTES de asignar el número, así que sin el flag
        #   el comprobante saldría como "Comprobante de Entrega" y paginaría distinto a lo que
        #   después se imprime; el flag fuerza el layout preimpreso e imprime la marca de línea.
        report = report.sudo().with_context(l10n_ar_counting=True)
        pdf_content, _dummy = report._render_qweb_pdf(report.id, self.ids)
        pdf_reader = PdfReader(BytesIO(pdf_content))
        copies = COPIES_BY_L10N_AR_COPIES.get(report.l10n_ar_copies, 1)
        pages_per_copy = max(1, len(pdf_reader.pages) // copies)
        return self._l10n_ar_count_pages_with_products(pdf_reader.pages[:pages_per_copy])

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
                # El CAI, su vencimiento y el rango no aplican al preimpreso: vienen impresos
                # en el papel de la imprenta. Igual escribimos las claves en False para
                # respetar la forma del dict que arma el core (l10n_ar_stock), porque los
                # reportes lo leen por subscript y un dict parcial los rompe con KeyError.
                self.l10n_ar_cai_data = {
                    "document_type_id": picking_type.l10n_ar_document_type_id.id,
                    "cai_authorization_code": False,
                    "cai_expiration_date": False,
                    "sequence_number_start": False,
                    "sequence_number_end": False,
                }
            return self.env.ref("stock.action_report_delivery").report_action(self)
        return super().l10n_ar_action_create_delivery_guide()
