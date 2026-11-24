from io import BytesIO
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.pdf import PdfFileWriter


@tagged("post_install", "-at_install")
class TestBatchPreprinted(TransactionCase):
    """Remito de un lote con cliente en un tipo de operación preimpreso."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.ar")
        cls.document_type = cls.env.ref("l10n_ar.dc_r_r")
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito test lote preimpreso",
                "sequence_code": "TESTBATPRE",
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
        cls.partner = cls.env["res.partner"].create({"name": "Cliente lote preimpreso test"})
        product = cls.env["product.product"].create({"name": "Producto lote preimpreso test", "type": "consu"})
        cls.pickings = cls.env["stock.picking"].create(
            [
                {
                    "picking_type_id": cls.picking_type.id,
                    "partner_id": cls.partner.id,
                    "location_id": cls.env.ref("stock.stock_location_stock").id,
                    "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                    "move_ids": [(0, 0, {"product_id": product.id, "product_uom_qty": 1.0})],
                }
                for __ in range(2)
            ]
        )
        cls.batch = cls.env["stock.picking.batch"].create(
            {
                "name": "Lote test remito preimpreso",
                "picking_type_id": cls.picking_type.id,
                "company_id": cls.env.company.id,
                "partner_id": cls.partner.id,
                "picking_ids": [(6, 0, cls.pickings.ids)],
            }
        )

    def _patch_pdf_pages(self, batch_pages, picking_pages=1):
        """Fake wkhtmltopdf: ``batch_pages`` blank pages for each body of the batch report and
        ``picking_pages`` for any other one, so the test tells which report was counted."""

        def fake_wkhtmltopdf(self_report, bodies, *args, **kwargs):
            writer = PdfFileWriter()
            for body in bodies:
                for __ in range(batch_pages if self.batch.name in str(body) else picking_pages):
                    writer.add_blank_page(width=595, height=842)
            stream = BytesIO()
            writer.write(stream)
            return stream.getvalue()

        return patch.object(type(self.env["ir.actions.report"]), "_run_wkhtmltopdf", fake_wkhtmltopdf)

    def _create_guide(self, batch_pages):
        # force_report_rendering: without it Odoo returns the HTML in tests and never calls
        # wkhtmltopdf, which is the step that builds the pages that are counted.
        with self._patch_pdf_pages(batch_pages):
            self.batch.with_context(force_report_rendering=True).l10n_ar_action_create_delivery_guide()

    def test_batch_is_numbered_by_the_sheets_of_its_report(self):
        """El remito del lote consume un número por hoja del reporte del lote, no de la
        primera entrega, y se copia igual en todas sus entregas."""
        sequence = self.picking_type.l10n_ar_sequence_id
        next_before = sequence.number_next_actual
        self.assertTrue(self.pickings[0].batch_partner_id)
        self._create_guide(batch_pages=3)
        numbers = self.pickings[0].l10n_ar_delivery_guide_number.split(",")
        self.assertEqual(len(numbers), 3)
        sequence_numbers = [int(number.split("-")[-1]) for number in numbers]
        self.assertEqual(sequence_numbers, list(range(sequence_numbers[0], sequence_numbers[0] + 3)))
        self.assertEqual(
            self.pickings.mapped("l10n_ar_delivery_guide_number"),
            [self.pickings[0].l10n_ar_delivery_guide_number] * 2,
        )
        self.assertEqual(self.batch.l10n_ar_delivery_guide_number, self.pickings[0].l10n_ar_delivery_guide_number)
        sequence.invalidate_recordset()
        self.assertEqual(sequence.number_next_actual, next_before + 3)

    def test_batch_cai_data_has_no_cai(self):
        """Como el remito preimpreso de una entrega: el CAI viene en el papel."""
        self._create_guide(batch_pages=1)
        for picking in self.pickings:
            self.assertFalse(picking.l10n_ar_cai_data["cai_authorization_code"])
        self.assertFalse(self.batch.l10n_ar_cai_expiration_date)

    def test_copies_do_not_multiply_sheets(self):
        """Un tipo en triplicado imprime el lote tres veces, pero cada hoja consume un solo número."""
        self.picking_type.l10n_ar_copies = "triplicado"
        with self._patch_pdf_pages(batch_pages=2):
            sheets = self.batch.with_context(force_report_rendering=True)._l10n_ar_count_preprinted_sheets()
        self.assertEqual(sheets, 2, "tres copias de dos hojas son seis páginas y dos hojas")

    def test_picking_without_batch_partner_keeps_its_own_count(self):
        """Una entrega fuera de un lote con cliente cuenta las hojas de su propio comprobante."""
        picking = self.pickings[0].copy({"batch_id": False})
        self.assertFalse(picking.batch_partner_id)
        with self._patch_pdf_pages(batch_pages=3):
            sheets = picking.with_context(force_report_rendering=True)._l10n_ar_count_preprinted_sheets()
        self.assertEqual(sheets, 1)

    def test_numbered_batch_prints_without_the_number(self):
        """Con el remito generado, el lote sale sin número (ya viene en el papel); en autoimpreso
        el mismo lote sí lo imprime."""
        self._create_guide(batch_pages=1)
        number = self.batch.l10n_ar_delivery_guide_number.encode()
        report = "stock_batch_picking_ux.action_report_batch_deliveryslip"
        html = self.env["ir.actions.report"]._render_qweb_html(report, self.batch.ids)[0]
        self.assertFalse(number in html, "el número no se imprime sobre el papel de imprenta")
        self.picking_type.write(
            {
                "l10n_ar_voucher_print_mode": "autoprinted",
                "l10n_ar_cai_authorization_code": "12345678901234",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "00000999",
            }
        )
        html = self.env["ir.actions.report"]._render_qweb_html(report, self.batch.ids)[0]
        self.assertTrue(number in html, "en autoimpreso el número sí se imprime")
