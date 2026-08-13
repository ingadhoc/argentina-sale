from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestL10nArBatchDeliveryReport(TransactionCase):
    """El comprobante de entrega del lote lee ``l10n_ar_cai_data`` del primer remito numerado.

    Ese dict puede no traer el código de CAI (un remito preimpreso no lo tiene: viene impreso
    en el papel de la imprenta) y el campo puede valer ``False`` cuando ningún remito del lote
    está numerado, porque es un ``fields.Json``. El pie tiene que aguantar los dos casos.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.ar")
        cls.document_type = cls.env.ref("l10n_ar.dc_r_r")
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito test lote",
                "sequence_code": "TESTBATREM",
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
        product = cls.env["product.product"].create({"name": "Producto lote test", "type": "consu"})
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "partner_id": cls.env["res.partner"].create({"name": "Cliente lote test"}).id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [(0, 0, {"product_id": product.id, "product_uom_qty": 1.0})],
            }
        )
        cls.batch = cls.env["stock.picking.batch"].create(
            {
                "name": "Lote test remito",
                "picking_type_id": cls.picking_type.id,
                "company_id": cls.env.company.id,
                "picking_ids": [(6, 0, cls.picking.ids)],
            }
        )

    def _render(self):
        return self.env["ir.actions.report"]._render_qweb_html(
            "stock_batch_picking_ux.action_report_batch_deliveryslip", self.batch.ids
        )[0]

    def _assert_no_cai_block(self):
        # comparamos así y no con assertNotIn para no volcar el HTML entero al fallar
        self.assertFalse(b"CAI:" in self._render(), "el pie no tiene que imprimir el bloque de CAI")

    def test_renders_without_cai_data(self):
        """Ningún remito del lote está numerado: l10n_ar_cai_data vale False."""
        self.assertFalse(self.batch.l10n_ar_cai_data)
        self._assert_no_cai_block()

    def test_uses_ar_report_without_delivery_guide_number(self):
        """El lote sin numerar también usa el comprobante argentino: las mismas
        transferencias impresas de a una ya salen así, el lote tiene que coincidir."""
        self.assertFalse(self.batch.l10n_ar_delivery_guide_number)
        self.assertEqual(
            self.batch._get_name_delivery_report("stock_batch_picking_ux.report_batch_delivery_document"),
            "l10n_ar_stock_picking_batch.report_batch_delivery_document",
        )

    def test_renders_as_plain_voucher_without_delivery_guide_number(self):
        """Sin número el comprobante argentino degrada solo: letra X y sin CAI."""
        html = self._render()
        self.assertIn(b"Comprobante de Entrega", html)
        self.assertIn(self.batch.name.encode(), html)
        self._assert_no_cai_block()

    def test_renders_with_cai_data_without_authorization_code(self):
        """Remito preimpreso adentro del lote: el dict no trae el código de CAI."""
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
        self.batch.invalidate_recordset()
        self._assert_no_cai_block()

    def test_renders_with_partial_cai_data(self):
        """Datos ya guardados en base: los remitos preimpresos numerados con la primera
        versión del módulo dejaron un dict con solo document_type_id, y ahí el lote rompía
        con KeyError: 'cai_authorization_code'."""
        self.picking.write(
            {
                "l10n_ar_delivery_guide_number": "00099-00000001",
                "l10n_ar_cai_data": {"document_type_id": self.document_type.id},
            }
        )
        self.batch.invalidate_recordset()
        self._assert_no_cai_block()

    def test_renders_with_full_cai_data(self):
        """Remito autoimpreso: el CAI sale impreso en el pie del lote."""
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
        self.batch.invalidate_recordset()
        html = self._render()
        self.assertIn(b"12345678901234", html)
