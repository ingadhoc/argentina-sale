from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger
from psycopg2 import IntegrityError


class TestCustomDeliveryReport(TransactionCase):
    """La plantilla propia del remito: cuándo reemplaza al comprobante estándar y qué vistas
    se aceptan como plantilla."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.ar")
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Remito test",
                "sequence_code": "TESTCUSTREM",
                "code": "outgoing",
                "company_id": cls.env.company.id,
                "warehouse_id": cls.env["stock.warehouse"]
                .search([("company_id", "=", cls.env.company.id)], limit=1)
                .id,
                "l10n_ar_document_type_id": cls.env.ref("l10n_ar.dc_r_r").id,
            }
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )
        # plantilla desde cero: el caso "formato", dibujada para la grilla del papel
        cls.custom_view = cls.env["ir.ui.view"].create(
            {
                "name": "Remito propio test",
                "type": "qweb",
                "arch": """
                    <t t-name="l10n_ar_stock_custom_report.remito_propio_test">
                        <t t-call="web.html_container">
                            <div class="page"><span t-field="o.name"/></div>
                        </t>
                    </t>
                """,
            }
        )

    def test_custom_template_replaces_standard_voucher(self):
        """Con plantilla propia el remito se imprime con esa vista, no con la estándar."""
        self.picking_type.l10n_ar_delivery_report_view_id = self.custom_view
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            self.custom_view.key,
        )

    def test_without_custom_template_keeps_standard_voucher(self):
        """Sin plantilla propia no cambia nada: sigue el comprobante argentino."""
        self.assertFalse(self.picking_type.l10n_ar_delivery_report_view_id)
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            "l10n_ar_stock_ux.report_delivery_document",
        )

    def test_custom_template_does_not_depend_on_the_country(self):
        """El hook no filtra por país: si el campo está cargado, se imprime con esa plantilla.
        Es lo que distingue este campo del flujo preimpreso, que sí es solo argentino."""
        self.env.company.country_id = self.env.ref("base.uy")
        self.picking_type.l10n_ar_delivery_report_view_id = self.custom_view
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            self.custom_view.key,
        )

    def test_custom_template_key_resolves_for_t_call(self):
        """El t-call resuelve los templates por key, así que el key tiene que existir y apuntar
        de vuelta a la vista. Odoo lo autogenera cuando la vista se crea sin key desde la
        interfaz, que es como la va a crear el consultor o el cliente."""
        self.assertTrue(self.custom_view.key)
        self.assertEqual(
            self.env["ir.ui.view"]._get_template_view(self.custom_view.key),
            self.custom_view,
        )

    def test_inheriting_primary_view_is_accepted(self):
        """El caso "campos": una vista primary que hereda el comprobante estándar se acepta y
        renderiza, porque Odoo aplica su diff sobre el arch del padre. Es el mismo patrón con el
        que el producto arma su propio comprobante argentino sobre el de stock."""
        inheriting_view = self.env["ir.ui.view"].create(
            {
                "name": "Remito con campos propios",
                "type": "qweb",
                "mode": "primary",
                "inherit_id": self.env.ref("l10n_ar_stock_ux.report_delivery_document").id,
                "arch": '<xpath expr="//div[@class=\'page\']" position="inside"><span/></xpath>',
            }
        )
        self.picking_type.l10n_ar_delivery_report_view_id = inheriting_view
        self.assertEqual(
            self.picking._get_name_delivery_report("stock.report_delivery_document"),
            inheriting_view.key,
        )

    def test_extension_view_is_rejected(self):
        """Una vista de modo 'extension' no tiene arch renderizable propio: el t-call imprimiría
        los nodos del diff sueltos, así que no la aceptamos como plantilla."""
        extension_view = self.env["ir.ui.view"].create(
            {
                "name": "Herencia del comprobante",
                "type": "qweb",
                "mode": "extension",
                "inherit_id": self.env.ref("l10n_ar_stock_ux.report_delivery_document").id,
                "arch": '<xpath expr="//div[@class=\'page\']" position="inside"><span/></xpath>',
            }
        )
        with self.assertRaises(ValidationError):
            self.picking_type.l10n_ar_delivery_report_view_id = extension_view

    def test_non_qweb_view_is_rejected(self):
        """Tampoco una vista de formulario: el campo apunta a templates de reporte."""
        with self.assertRaises(ValidationError):
            self.picking_type.l10n_ar_delivery_report_view_id = self.env.ref("stock.view_picking_form")

    @mute_logger("odoo.sql_db")
    def test_view_in_use_cannot_be_deleted(self):
        """Borrar la plantilla dejaría el tipo de operación imprimiendo un template inexistente,
        así que el campo es ondelete restrict."""
        self.picking_type.l10n_ar_delivery_report_view_id = self.custom_view
        self.env.flush_all()
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.custom_view.unlink()
