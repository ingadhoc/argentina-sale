from base64 import b64encode

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

TEMPLATE = b64encode(b"plantilla odt de prueba")


class TestPreprintedAeroo(TransactionCase):
    """El reemplazo del comprobante qweb por la plantilla .odt del talonario, y el conteo de hojas
    por renglones que va con él."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type = cls.env.ref("l10n_ar.dc_r_r")
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito preimpreso aeroo test",
                "sequence_code": "TESTAEROO",
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
        cls.product = cls.env["product.product"].create({"name": "Producto aeroo test", "type": "consu"})
        cls.delivery_report = cls.env.ref("stock.action_report_delivery")
        cls.aeroo_report = cls.env.ref("l10n_ar_stock_preprinted_aeroo.report_delivery_preprinted_aeroo")

    def _picking(self, lines=1, picking_type=None):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": (picking_type or self.picking_type).id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1.0}) for __ in range(lines)],
            }
        )

    def _load_template(self, lines_per_sheet=10):
        self.picking_type.write(
            {
                "l10n_ar_preprinted_template": TEMPLATE,
                "l10n_ar_preprinted_lines_per_sheet": lines_per_sheet,
            }
        )

    # === la plantilla solo aplica en preimpreso === #

    def test_template_needs_preprinted_mode(self):
        """Una plantilla cargada en un tipo autoimpreso no aplica: ahí Odoo imprime el comprobante
        completo y la plantilla del talonario no trae encabezado ni CAI."""
        self._load_template()
        # el autoimpreso exige los datos de CAI, que en preimpreso vienen impresos en el papel
        self.picking_type.write(
            {
                "l10n_ar_voucher_print_mode": "autoprinted",
                "l10n_ar_cai_authorization_code": "12345678901234",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "00001000",
            }
        )
        self.assertFalse(self._picking()._l10n_ar_preprinted_aeroo_template())

    def test_no_template_keeps_qweb(self):
        """Sin plantilla cargada no cambia nada: sigue el comprobante de entrega de siempre."""
        picking = self._picking()
        self.assertFalse(picking._l10n_ar_preprinted_aeroo_template())
        self.assertFalse(self.delivery_report._l10n_ar_preprinted_aeroo_report(picking))

    # === reemplazo del reporte === #

    def test_template_replaces_delivery_report(self):
        """Con plantilla cargada, imprimir el comprobante de entrega imprime el reporte aeroo."""
        self._load_template()
        picking = self._picking()
        self.assertEqual(self.delivery_report._l10n_ar_preprinted_aeroo_report(picking), self.aeroo_report)
        # config=False para no caer en el wizard de layout de la compañía, que envuelve la acción
        action = self.delivery_report.report_action(picking, config=False)
        self.assertEqual(action["report_name"], self.aeroo_report.report_name)

    def test_other_reports_untouched(self):
        """El reemplazo es solo del comprobante de entrega: cualquier otro reporte se imprime como
        siempre, aunque el remito tenga plantilla."""
        self._load_template()
        picking = self._picking()
        other_report = self.env.ref("stock.action_report_picking")
        self.assertFalse(other_report._l10n_ar_preprinted_aeroo_report(picking))

    def test_mixed_picking_types_keep_qweb(self):
        """Un lote con dos talonarios distintos no tiene un reporte que sirva para los dos: se
        imprime el comprobante qweb, que es el comportamiento de siempre."""
        self._load_template()
        other_type = self.picking_type.copy({"name": "Otro talonario", "sequence_code": "TESTAEROO2"})
        pickings = self._picking() | self._picking(picking_type=other_type)
        self.assertFalse(self.delivery_report._l10n_ar_preprinted_aeroo_report(pickings))

    def test_one_picking_without_template_keeps_qweb(self):
        """Si en el lote hay un remito sin plantilla, el lote entero sale por qweb."""
        self._load_template()
        picking = self._picking()
        self.picking_type.l10n_ar_preprinted_template = False
        self.assertFalse(self.delivery_report._l10n_ar_preprinted_aeroo_report(picking))

    # === la plantilla sale del tipo de operación === #

    def test_parser_reads_template_from_picking_type(self):
        """El parser de aeroo resuelve la plantilla contra el remito que se está imprimiendo, así
        un solo reporte sirve para todos los talonarios del cliente."""
        self._load_template()
        parser = self.env["report.l10n_ar_preprinted_aeroo"]
        self.assertEqual(parser.get_template(self._picking()), b"plantilla odt de prueba")

    # === conteo de hojas por renglones === #

    def test_sheets_by_lines_per_sheet(self):
        """Las hojas salen de los renglones, no de renderizar: 25 renglones a 10 por hoja son 3."""
        self._load_template(lines_per_sheet=10)
        self.assertEqual(self._picking(lines=25)._l10n_ar_count_preprinted_sheets(), 3)

    def test_sheets_exact_multiple(self):
        """Un remito que llena las hojas justas no arrastra una hoja de más."""
        self._load_template(lines_per_sheet=10)
        self.assertEqual(self._picking(lines=20)._l10n_ar_count_preprinted_sheets(), 2)

    def test_sheets_minimum_one(self):
        """Un remito sin renglones consume igual una hoja: la del papel que se imprimió."""
        self._load_template(lines_per_sheet=10)
        self.assertEqual(self._picking(lines=0)._l10n_ar_count_preprinted_sheets(), 1)

    def test_numbering_uses_one_number_per_sheet(self):
        """El remito toma un número por hoja consumida, como el flujo preimpreso de siempre, pero
        con las hojas calculadas."""
        self._load_template(lines_per_sheet=10)
        picking = self._picking(lines=25)
        picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(len(picking.l10n_ar_delivery_guide_number.split(",")), 3)

    # === la validación de renglones por hoja === #

    def test_template_requires_lines_per_sheet(self):
        """Sin renglones por hoja el conteo daría siempre una hoja y el remito consumiría un solo
        número aunque ocupe varias."""
        with self.assertRaises(ValidationError):
            self.picking_type.l10n_ar_preprinted_template = TEMPLATE

    def test_lines_per_sheet_not_required_without_template(self):
        """Sin plantilla el campo no se pide: las hojas se cuentan renderizando el qweb."""
        self.picking_type.l10n_ar_preprinted_lines_per_sheet = 0
        self.assertFalse(self.picking_type.l10n_ar_preprinted_template)
