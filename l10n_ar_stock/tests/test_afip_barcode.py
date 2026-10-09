##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.l10n_ar.tests.common import TestArCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAfipBarcode(TestArCommon):
    """El código de barras del remito auto-impresor sale del punto de venta del talonario.

    El punto de venta se toma de los dígitos del prefijo de la secuencia. Un prefijo sin
    dígitos no tiene punto de venta, y en ese caso el remito se imprime sin código de barras
    en lugar de romper el reporte.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type = cls.env.ref("l10n_ar.dc_r_r")
        cls.picking_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.company_ri.id)], limit=1
        )

    def _create_book(self, prefix):
        sequence = self.env["ir.sequence"].create(
            {
                "name": "Test Remito %s" % prefix,
                "code": "stock.voucher",
                "prefix": prefix,
                "padding": 8,
                "company_id": self.company_ri.id,
            }
        )
        return self.env["stock.book"].create(
            {
                "name": "Test Book %s" % prefix,
                "sequence_id": sequence.id,
                "lines_per_voucher": 0,
                "company_id": self.company_ri.id,
                "document_type_id": self.document_type.id,
                "l10n_ar_cai": "12345678901234",
                "l10n_ar_cai_due": "2030-12-31",
            }
        )

    def _create_picking(self, prefix):
        return self.env["stock.picking"].create(
            {
                "partner_id": self.res_partner_adhoc.id,
                "picking_type_id": self.picking_type.id,
                "book_id": self._create_book(prefix).id,
                "company_id": self.company_ri.id,
            }
        )

    def test_barcode_with_point_of_sale_in_prefix(self):
        picking = self._create_picking("R-00010-")
        self.assertEqual(picking.l10n_ar_afip_barcode, "30111111118091000101234567890123420301231")

    def test_no_barcode_when_prefix_has_no_digits(self):
        """Un prefijo sin dígitos no da punto de venta: sin código de barras y sin error."""
        self.assertFalse(self._create_picking("R-").l10n_ar_afip_barcode)

    def test_no_barcode_when_prefix_is_empty(self):
        self.assertFalse(self._create_picking("").l10n_ar_afip_barcode)
