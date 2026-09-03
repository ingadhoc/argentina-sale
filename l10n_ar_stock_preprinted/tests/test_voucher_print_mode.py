from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


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
