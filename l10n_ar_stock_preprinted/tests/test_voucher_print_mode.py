from io import BytesIO
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools.pdf import PdfWriter

from ..models.stock_picking import L10N_AR_PREPRINTED_LINE_MARK


def _pdf_with_pages(pages):
    """PDF en blanco de ``pages`` páginas, para no depender de wkhtmltopdf."""
    writer = PdfWriter()
    for __ in range(pages):
        writer.add_blank_page(width=595, height=842)
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


class PreprintedCommon(TransactionCase):
    """Tipo de operación preimpreso con un remito de una línea, base de los dos casos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type = cls.env.ref("l10n_ar.dc_r_r")
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito test",
                "sequence_code": "TESTREM",
                "code": "outgoing",
                "company_id": cls.env.company.id,
                "warehouse_id": cls.env["stock.warehouse"]
                .search([("company_id", "=", cls.env.company.id)], limit=1)
                .id,
                "l10n_ar_document_type_id": cls.document_type.id,
                "l10n_ar_voucher_print_mode": "preprinted",
            }
        )
        cls.picking_type.l10n_ar_delivery_sequence_prefix = "00099"
        cls.product = cls.env["product.product"].create({"name": "Producto remito test", "type": "consu"})
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1.0,
                        },
                    )
                ],
            }
        )


class TestVoucherPrintMode(PreprintedCommon):
    """El modo de impresión del remito y la numeración que se deriva de él."""

    def test_preprinted_allows_empty_cai(self):
        """En preimpreso el CAI y el rango no se cargan: vienen impresos en el papel."""
        self.assertFalse(self.picking_type.l10n_ar_cai_authorization_code)
        # no debería levantar la restricción
        self.picking_type.write({"l10n_ar_voucher_print_mode": "preprinted"})
        self.assertEqual(self.picking_type.l10n_ar_voucher_print_mode, "preprinted")

    def test_autoprinted_requires_cai(self):
        """En autoimpreso Odoo imprime el CAI, así que el CAI y su rango son obligatorios
        incluso escribiendo por ORM (donde el required de la vista no aplica)."""
        with self.assertRaises(ValidationError):
            self.picking_type.write({"l10n_ar_voucher_print_mode": "autoprinted"})

    def test_autoprinted_with_cai_is_valid(self):
        self.picking_type.write(
            {
                "l10n_ar_voucher_print_mode": "autoprinted",
                "l10n_ar_cai_authorization_code": "12345678901234",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "00000999",
            }
        )
        self.assertEqual(self.picking_type.l10n_ar_voucher_print_mode, "autoprinted")

    def test_print_mode_default_is_autoprinted(self):
        """Los tipos de operación existentes y los nuevos siguen siendo autoimpresos."""
        picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Sin remito",
                "sequence_code": "TESTNOREM",
                "code": "internal",
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(picking_type.l10n_ar_voucher_print_mode, "autoprinted")

    def test_preprinted_numbering_one_number_per_sheet(self):
        """El preimpreso asigna un número por hoja consumida, separados por coma y sin CAI."""
        with patch.object(type(self.picking), "_l10n_ar_count_preprinted_sheets", return_value=3):
            self.picking.l10n_ar_action_create_delivery_guide()
        numbers = self.picking.l10n_ar_delivery_guide_number.split(",")
        self.assertEqual(len(numbers), 3)
        # los números tienen la forma <prefijo>-<8 dígitos>: comparamos la parte numérica
        # contra un range para verificar que sean consecutivos y sin huecos
        sequence_numbers = [int(number.split("-")[-1]) for number in numbers]
        self.assertEqual(
            sequence_numbers,
            list(range(sequence_numbers[0], sequence_numbers[0] + 3)),
            "los números deben ser consecutivos y sin huecos",
        )
        self.assertEqual(
            self.picking.l10n_ar_cai_data,
            {"document_type_id": self.document_type.id},
            "en preimpreso no se guardan datos de CAI: vienen impresos en el papel",
        )

    def test_preprinted_numbering_is_idempotent(self):
        """Reimprimir no consume números nuevos."""
        with patch.object(type(self.picking), "_l10n_ar_count_preprinted_sheets", return_value=2):
            self.picking.l10n_ar_action_create_delivery_guide()
            numbers = self.picking.l10n_ar_delivery_guide_number
            self.picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(self.picking.l10n_ar_delivery_guide_number, numbers)

    def test_sheet_count_ignores_report_copies(self):
        """El reporte repite el comprobante una vez por copia (duplicado / triplicado) y el
        juego de copias consume un solo número por hoja: 6 páginas en triplicado son 2 hojas."""
        report = self.env.ref("stock.action_report_delivery")
        report.l10n_ar_copies = "triplicado"
        with (
            patch.object(type(report), "_render_qweb_pdf", return_value=(_pdf_with_pages(6), "pdf")),
            patch.object(type(self.picking), "_l10n_ar_count_pages_with_products", return_value=6),
        ):
            self.assertEqual(self.picking._l10n_ar_count_preprinted_sheets(), 2)

    def test_sheet_count_without_copies(self):
        report = self.env.ref("stock.action_report_delivery")
        report.l10n_ar_copies = False
        with (
            patch.object(type(report), "_render_qweb_pdf", return_value=(_pdf_with_pages(2), "pdf")),
            patch.object(type(self.picking), "_l10n_ar_count_pages_with_products", return_value=2),
        ):
            self.assertEqual(self.picking._l10n_ar_count_preprinted_sheets(), 2)

    def test_preprinted_forces_ar_delivery_report(self):
        """Un tipo preimpreso usa el comprobante argentino aunque todavía NO tenga número de
        remito: sin número se imprime como comprobante de entrega normal (no el remito de
        Odoo) y el conteo de hojas fuerza el layout preimpreso; los dos necesitan el template
        argentino. El core de l10n_ar_stock_ux solo lo elige cuando ya hay número."""
        self.picking.company_id.country_id = self.env.ref("base.ar")
        self.assertFalse(self.picking.l10n_ar_delivery_guide_number)
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            "l10n_ar_stock_ux.report_delivery_document",
        )

    def test_count_pages_by_line_mark(self):
        """El contador cuenta solo las páginas que traen la marca de línea de producto: una
        hoja de solo transportista / firma / totales (sin marca) no consume número."""

        class _Page:
            def __init__(self, text):
                self._text = text

            def extract_text(self):
                return self._text

        class _Reader:
            def __init__(self, pages):
                self.pages = pages

        reader = _Reader(
            [
                _Page("Producto A " + L10N_AR_PREPRINTED_LINE_MARK),
                _Page("Producto B " + L10N_AR_PREPRINTED_LINE_MARK),
                _Page("Datos del transportista, sin líneas de producto"),
            ]
        )
        self.assertEqual(self.picking._l10n_ar_count_pages_with_products(reader), 2)


class TestCustomPreprintedTemplate(PreprintedCommon):
    """Plantilla QWeb propia por tipo de operación: reemplaza el comprobante estándar y
    cambia el criterio de conteo de hojas."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.custom_view = cls.env["ir.ui.view"].create(
            {
                "name": "Remito preimpreso propio",
                "type": "qweb",
                "arch": """
                    <t t-name="l10n_ar_stock_preprinted.remito_propio_test">
                        <t t-call="web.html_container">
                            <div class="page"><span t-field="o.name"/></div>
                        </t>
                    </t>
                """,
            }
        )

    def test_custom_template_replaces_standard_voucher(self):
        """Con plantilla propia el comprobante se imprime con esa vista, no con la estándar."""
        self.picking.company_id.country_id = self.env.ref("base.ar")
        self.picking_type.l10n_ar_preprinted_report_view_id = self.custom_view
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            self.custom_view.key,
        )

    def test_custom_template_key_resolves_for_t_call(self):
        """El t-call resuelve los templates por key, así que el key tiene que existir y apuntar
        de vuelta a la vista. Odoo lo autogenera cuando la vista se crea sin key desde la
        interfaz, que es como la va a crear el consultor."""
        self.assertTrue(self.custom_view.key)
        self.assertEqual(
            self.env["ir.ui.view"]._get_template_view(self.custom_view.key),
            self.custom_view,
        )

    def test_without_custom_template_keeps_standard_voucher(self):
        """Sin plantilla propia no cambia nada: sigue el comprobante argentino."""
        self.picking.company_id.country_id = self.env.ref("base.ar")
        self.assertFalse(self.picking_type.l10n_ar_preprinted_report_view_id)
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            "l10n_ar_stock_ux.report_delivery_document",
        )

    def test_custom_template_only_applies_to_preprinted(self):
        """En autoimpreso la plantilla propia no aplica: el campo es del flujo preimpreso."""
        self.picking_type.l10n_ar_preprinted_report_view_id = self.custom_view
        self.picking_type.write(
            {
                "l10n_ar_voucher_print_mode": "autoprinted",
                "l10n_ar_cai_authorization_code": "12345678901234",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "00000999",
            }
        )
        self.picking.company_id.country_id = self.env.ref("base.ar")
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            "l10n_ar_stock_ux.report_delivery_document",
        )

    def test_custom_template_counts_every_page(self):
        """Con plantilla propia toda página impresa es una hoja del talonario: no se descuenta
        ninguna aunque no traiga la marca de línea (una plantilla desde cero no la emite)."""
        self.picking_type.l10n_ar_preprinted_report_view_id = self.custom_view
        report = self.env.ref("stock.action_report_delivery")
        report.l10n_ar_copies = False
        with patch.object(type(report), "_render_qweb_pdf", return_value=(_pdf_with_pages(3), "pdf")):
            self.assertEqual(self.picking._l10n_ar_count_preprinted_sheets(), 3)

    def test_custom_template_page_count_ignores_copies(self):
        """El juego de copias sigue consumiendo un solo número por hoja."""
        self.picking_type.l10n_ar_preprinted_report_view_id = self.custom_view
        report = self.env.ref("stock.action_report_delivery")
        report.l10n_ar_copies = "triplicado"
        with patch.object(type(report), "_render_qweb_pdf", return_value=(_pdf_with_pages(6), "pdf")):
            self.assertEqual(self.picking._l10n_ar_count_preprinted_sheets(), 2)

    def test_custom_template_does_not_use_line_mark(self):
        """El conteo por marca de línea queda fuera de juego con plantilla propia: si siguiera
        vigente, una plantilla sin marca daría una sola hoja para un remito de tres."""
        self.picking_type.l10n_ar_preprinted_report_view_id = self.custom_view
        report = self.env.ref("stock.action_report_delivery")
        report.l10n_ar_copies = False
        with (
            patch.object(type(report), "_render_qweb_pdf", return_value=(_pdf_with_pages(3), "pdf")),
            patch.object(type(self.picking), "_l10n_ar_count_pages_with_products", return_value=1),
        ):
            self.assertEqual(self.picking._l10n_ar_count_preprinted_sheets(), 3)

    def test_custom_template_numbering_uses_page_count(self):
        """Punta a punta: tres páginas impresas consumen tres números del talonario."""
        self.picking_type.l10n_ar_preprinted_report_view_id = self.custom_view
        report = self.env.ref("stock.action_report_delivery")
        report.l10n_ar_copies = False
        with patch.object(type(report), "_render_qweb_pdf", return_value=(_pdf_with_pages(3), "pdf")):
            self.picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(len(self.picking.l10n_ar_delivery_guide_number.split(",")), 3)

    def test_extension_view_is_rejected(self):
        """Una vista de herencia no tiene arch renderizable propio: el t-call imprimiría los
        nodos del diff sueltos, así que no la aceptamos como plantilla."""
        extension = self.env["ir.ui.view"].create(
            {
                "name": "Herencia del comprobante",
                "type": "qweb",
                "mode": "extension",
                "inherit_id": self.env.ref("l10n_ar_stock_ux.report_delivery_document").id,
                "arch": '<xpath expr="//div[@class=\'page\']" position="inside"><span/></xpath>',
            }
        )
        with self.assertRaises(ValidationError):
            self.picking_type.l10n_ar_preprinted_report_view_id = extension

    def test_non_qweb_view_is_rejected(self):
        """Tampoco una vista de formulario: el campo apunta a templates de reporte."""
        form_view = self.env.ref("stock.view_picking_form")
        with self.assertRaises(ValidationError):
            self.picking_type.l10n_ar_preprinted_report_view_id = form_view
