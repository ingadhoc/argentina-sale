from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestL10nArStockUxDeliveryReport(TransactionCase):
    """El comprobante de entrega argentino se usa para TODA transferencia de compañía AR,
    tenga o no remito generado, así que tiene que renderizar sin datos de CAI.

    ``l10n_ar_cai_data`` es un ``fields.Json``: con la columna en NULL el ORM devuelve
    ``False`` (no un dict vacío), y además un remito preimpreso no guarda el código de CAI
    porque viene impreso en el papel. El pie del comprobante tiene que aguantar los dos casos.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.ar")
        cls.document_type = cls.env.ref("l10n_ar.dc_r_r")
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito test reporte",
                "sequence_code": "TESTREPREM",
                "code": "outgoing",
                "company_id": cls.env.company.id,
                "warehouse_id": cls.env["stock.warehouse"]
                .search([("company_id", "=", cls.env.company.id)], limit=1)
                .id,
                "l10n_ar_document_type_id": cls.document_type.id,
                # tipo autoimpreso normal: Odoo imprime el CAI, así que va configurado
                "l10n_ar_cai_authorization_code": "12345678901234",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "00000999",
            }
        )
        product = cls.env["product.product"].create({"name": "Producto reporte test", "type": "consu"})
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "partner_id": cls.env["res.partner"].create({"name": "Cliente reporte test"}).id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [(0, 0, {"product_id": product.id, "product_uom_qty": 1.0})],
            }
        )

    def _render(self):
        return self.env["ir.actions.report"]._render_qweb_html("stock.action_report_delivery", self.picking.ids)[0]

    def _assert_no_cai_block(self):
        # comparamos así y no con assertNotIn para no volcar el HTML entero al fallar
        self.assertFalse(b"CAI:" in self._render(), "el pie no tiene que imprimir el bloque de CAI")

    def test_renders_without_cai_data(self):
        """Sin remito generado no hay datos de CAI y el campo Json vale False."""
        self.assertFalse(self.picking.l10n_ar_cai_data)
        self._assert_no_cai_block()

    def test_renders_with_cai_data_without_authorization_code(self):
        """Remito preimpreso: el dict trae las claves pero el CAI viene en blanco."""
        self.picking.write(
            {
                "l10n_ar_delivery_guide_number": "00099-00000001",
                "l10n_ar_cai_data": {
                    "document_type_id": self.document_type.id,
                    "cai_authorization_code": False,
                    "cai_expiration_date": False,
                    "sequence_number_start": False,
                    "sequence_number_end": False,
                },
            }
        )
        self._assert_no_cai_block()

    def test_renders_with_partial_cai_data(self):
        """Datos ya guardados en base: los remitos preimpresos numerados con la primera
        versión del módulo dejaron un dict con solo document_type_id. El reporte no puede
        romper con esos registros."""
        self.picking.write(
            {
                "l10n_ar_delivery_guide_number": "00099-00000001",
                "l10n_ar_cai_data": {"document_type_id": self.document_type.id},
            }
        )
        self._assert_no_cai_block()

    def test_renders_with_full_cai_data(self):
        """Remito autoimpreso: el CAI y su vencimiento salen impresos."""
        self.picking.write(
            {
                "l10n_ar_delivery_guide_number": "00099-00000001",
                "l10n_ar_cai_data": {
                    "document_type_id": self.document_type.id,
                    "cai_authorization_code": "12345678901234",
                    "cai_expiration_date": "2030-12-31",
                    "sequence_number_start": "00000001",
                    "sequence_number_end": "00000999",
                },
            }
        )
        html = self._render()
        self.assertIn(b"12345678901234", html)
