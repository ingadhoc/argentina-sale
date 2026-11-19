from io import BytesIO
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools.pdf import PdfFileWriter


class TestVoucherPrintMode(TransactionCase):
    """El modo de impresión del remito y la numeración que se deriva de él."""

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
        cls._validate(cls.picking)

    @classmethod
    def _validate(cls, picking):
        # the delivery guide is generated only on validated transfers
        picking.company_id.stock_move_email_validation = False
        picking.action_confirm()
        picking.button_validate()

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

    def test_autoprinted_remito_x_allows_empty_cai(self):
        """El CAI aplica solo a los remitos clase R: un Remito X autoimpreso se guarda, se
        numera y queda sin datos de CAI."""
        picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Remito X test",
                "sequence_code": "TESTREMX",
                "code": "outgoing",
                "company_id": self.env.company.id,
                "warehouse_id": self.picking_type.warehouse_id.id,
                "l10n_ar_document_type_id": self.env.ref("l10n_ar.dc_remito_x").id,
                "l10n_ar_voucher_print_mode": "autoprinted",
            }
        )
        self.assertFalse(picking_type.l10n_ar_cai_required)
        picking_type.l10n_ar_delivery_sequence_prefix = "00098"
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1.0})],
            }
        )
        self._validate(picking)
        picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(picking.l10n_ar_delivery_guide_number, "00098-00000001")
        self.assertFalse(picking.l10n_ar_cai_data["cai_authorization_code"])

    def test_cai_required_only_on_autoprinted_remito_r(self):
        self.assertFalse(self.picking_type.l10n_ar_cai_required, "preimpreso: el CAI viene en el papel")
        self.picking_type.l10n_ar_document_type_id = self.env.ref("l10n_ar.dc_remito_x")
        self.picking_type.l10n_ar_voucher_print_mode = "autoprinted"
        self.assertFalse(self.picking_type.l10n_ar_cai_required, "el Remito X no lleva CAI")
        self.picking_type.write(
            {
                "l10n_ar_document_type_id": self.document_type.id,
                "l10n_ar_cai_authorization_code": "12345678901234",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "00000999",
            }
        )
        self.assertTrue(self.picking_type.l10n_ar_cai_required, "el Remito R autoimpreso lleva CAI")
        with self.assertRaises(ValidationError):
            self.picking_type.l10n_ar_cai_authorization_code = False

    def test_cai_format_not_checked_on_preprinted(self):
        """En preimpreso el CAI no se ve en el formulario: uno viejo que no cumple no puede
        trabar la edición del tipo de operación."""
        self.env.cr.execute(
            "UPDATE stock_picking_type SET l10n_ar_cai_authorization_code = %s WHERE id = %s",
            ("1234567890", self.picking_type.id),
        )
        self.picking_type.invalidate_recordset(["l10n_ar_cai_authorization_code"])
        # at_install tests run while the registry is loading, when the check is skipped
        with patch.object(self.env.registry, "ready", True):
            self.picking_type.name = "Remito test renamed"
        self.assertEqual(self.picking_type.name, "Remito test renamed")

    def test_preprinted_without_prefix_raises_clear_error(self):
        """Sin prefijo no se numera: error claro en vez de números sin punto de venta."""
        self.picking_type.l10n_ar_sequence_id.prefix = False
        self.picking_type.invalidate_recordset(["l10n_ar_delivery_sequence_prefix"])
        with self.assertRaisesRegex(UserError, "has no delivery guide prefix"):
            self.picking.l10n_ar_action_create_delivery_guide()
        self.assertFalse(self.picking.l10n_ar_delivery_guide_number)

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

    def test_preprinted_cai_data_keeps_core_shape(self):
        """El dict de CAI lleva las mismas claves que escribe el core, con los datos del CAI
        en False: vienen impresos en el papel. Un dict parcial rompe con KeyError los reportes
        que lo leen por subscript (comprobante de entrega, lote y guía de Odoo)."""
        with patch.object(type(self.picking), "_l10n_ar_count_preprinted_sheets", return_value=1):
            self.picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(
            self.picking.l10n_ar_cai_data,
            {
                "document_type_id": self.document_type.id,
                "cai_authorization_code": False,
                "cai_expiration_date": False,
                "sequence_number_start": False,
                "sequence_number_end": False,
            },
        )
        # y no se cuela ningún dato de CAI en el comprobante
        self.assertFalse(self.picking.l10n_ar_cai_expiration_date)
        self.assertFalse(self.picking.l10n_ar_afip_barcode)

    def test_preprinted_numbering_is_idempotent(self):
        """Reimprimir no consume números nuevos."""
        with patch.object(type(self.picking), "_l10n_ar_count_preprinted_sheets", return_value=2):
            self.picking.l10n_ar_action_create_delivery_guide()
            numbers = self.picking.l10n_ar_delivery_guide_number
            self.picking.l10n_ar_action_create_delivery_guide()
        self.assertEqual(self.picking.l10n_ar_delivery_guide_number, numbers)

    def _new_picking(self, validate=True):
        # stock_ux blocks copy() on a picking type with "Block Additional Quantity"
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1.0})],
            }
        )
        if validate:
            self._validate(picking)
        return picking

    def test_preprinted_several_pickings_warn_without_numbering(self):
        """Con varias entregas juntas (lista o lote) no se numera ni se da un error técnico:
        el número viene impreso en el papel y tendría que salir en el mismo orden."""
        pickings = self.picking | self._new_picking()
        with self.assertRaisesRegex(UserError, "one picking at a time"):
            pickings.l10n_ar_action_create_delivery_guide()
        self.assertFalse(any(pickings.mapped("l10n_ar_delivery_guide_number")))

    def test_preprinted_not_validated_is_not_numbered(self):
        """Desde la lista llega cualquier entrega: sin validar no se numera, porque cada
        número gastado quema una hoja del talonario."""
        picking = self._new_picking(validate=False)
        with self.assertRaisesRegex(UserError, "Validate the picking"):
            picking.l10n_ar_action_create_delivery_guide()
        self.assertFalse(picking.l10n_ar_delivery_guide_number)

    def test_preprinted_auto_assign_on_validation(self):
        """Al validar, un tipo con autoasignación numera la entrega preimpresa por sus hojas."""
        self.picking_type.auto_assign_delivery_guide = True
        picking = self._new_picking(validate=False)
        with patch.object(type(picking), "_l10n_ar_count_preprinted_sheets", return_value=2):
            self._validate(picking)
        self.assertEqual(len(picking.l10n_ar_delivery_guide_number.split(",")), 2)

    def test_autoprinted_several_pickings_use_standard_flow(self):
        """El aviso es solo del preimpreso: en autoimpreso varias entregas siguen yendo al
        flujo estándar de Odoo."""
        self.picking_type.write(
            {
                "l10n_ar_voucher_print_mode": "autoprinted",
                "l10n_ar_cai_authorization_code": "12345678901234",
                "l10n_ar_cai_expiration_date": "2030-12-31",
                "l10n_ar_sequence_number_start": "00000001",
                "l10n_ar_sequence_number_end": "00000999",
            }
        )
        pickings = self.picking | self._new_picking()
        pickings.l10n_ar_action_create_delivery_guide()
        self.assertTrue(all(pickings.mapped("l10n_ar_delivery_guide_number")))

    def test_preprinted_uses_ar_delivery_report(self):
        """Toda transferencia de compañía AR se imprime con el comprobante argentino, tenga o
        no número de remito asignado (l10n_ar_stock_ux). El preimpreso lo necesita también
        antes de numerar, porque el conteo de hojas renderiza ese mismo comprobante."""
        self.picking.company_id.country_id = self.env.ref("base.ar")
        self.assertFalse(self.picking.l10n_ar_delivery_guide_number)
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            "l10n_ar_stock_ux.report_delivery_document",
        )

    def test_preprinted_sheets_ignore_operation_type_copies(self):
        """El juego de copias consume un solo número por hoja: un tipo en triplicado imprime el
        comprobante tres veces pero numera una sola hoja."""
        self.picking.company_id.country_id = self.env.ref("base.ar")
        self.picking.partner_id = self.env["res.partner"].create({"name": "Cliente remito test"})
        self.picking_type.l10n_ar_copies = "triplicado"
        rendered_bodies = []

        def fake_pdf_engine(self_report, engine_name, bodies, *args, **kwargs):
            # one blank page per body: each copy of the voucher is its own body
            rendered_bodies.append(len(bodies))
            writer = PdfFileWriter()
            for __ in bodies:
                writer.add_blank_page(width=595, height=842)
            stream = BytesIO()
            writer.write(stream)
            return stream.getvalue()

        # force_report_rendering: sin eso, en tests Odoo devuelve el HTML y nunca llama al
        # motor de PDF, que es el paso que arma las páginas que se cuentan.
        # El estado del motor también se parchea: en el CI no hay wkhtmltopdf y el core
        # corta antes de llegar al motor falso.
        report_model = type(self.env["ir.actions.report"])
        with (
            patch.object(report_model, "get_pdf_engine_state", return_value="ok"),
            patch.object(report_model, "_run_pdf_engine_without_processing", fake_pdf_engine),
        ):
            sheets = self.picking.with_context(force_report_rendering=True)._l10n_ar_count_preprinted_sheets()
        self.assertEqual(rendered_bodies, [3], "el comprobante tendría que salir tres veces")
        self.assertEqual(sheets, 1)
