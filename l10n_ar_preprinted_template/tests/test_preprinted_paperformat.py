from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestPreprintedPaperformat(TransactionCase):
    """El formato de papel propio del remito preimpreso: cuándo gana sobre el del reporte, cuándo
    no se aplica, y qué pasa si se imprimen juntas transferencias con geometrías distintas."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.ar")
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.report = cls.env.ref("stock.action_report_delivery")
        # Plantilla propia mínima: el foco de estos tests es la geometría, no el contenido.
        cls.custom_view = cls.env["ir.ui.view"].create(
            {
                "name": "Remito propio paperformat test",
                "type": "qweb",
                "arch": """
                    <t t-name="l10n_ar_preprinted_template.remito_paperformat_test">
                        <t t-call="web.html_container">
                            <div class="page"><span t-field="o.name"/></div>
                        </t>
                    </t>
                """,
            }
        )
        # El talonario de la imprenta: A4 a sangre, sin achicado automático.
        cls.paperformat = cls.env["report.paperformat"].create(
            {
                "name": "Talonario test",
                "format": "A4",
                "orientation": "Portrait",
                "margin_top": 0,
                "margin_bottom": 0,
                "margin_left": 0,
                "margin_right": 0,
                "header_spacing": 0,
                "disable_shrinking": True,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Cliente remito test"})
        cls.picking_type = cls._create_picking_type("preprinted", "TESTPREPF")
        cls.picking_type.l10n_ar_delivery_report_view_id = cls.custom_view
        cls.picking_type.l10n_ar_delivery_paperformat_id = cls.paperformat
        cls.picking = cls._create_picking(cls.picking_type)

    @classmethod
    def _create_picking_type(cls, print_mode, sequence_code):
        vals = {
            "name": "Remito %s test" % print_mode,
            "sequence_code": sequence_code,
            "code": "outgoing",
            "company_id": cls.env.company.id,
            "warehouse_id": cls.warehouse.id,
            "l10n_ar_document_type_id": cls.env.ref("l10n_ar.dc_r_r").id,
            "l10n_ar_voucher_print_mode": print_mode,
        }
        if print_mode == "autoprinted":
            vals.update(
                {
                    "l10n_ar_cai_authorization_code": "12345678901234",
                    "l10n_ar_cai_expiration_date": "2030-12-31",
                    "l10n_ar_sequence_number_start": "00000001",
                    "l10n_ar_sequence_number_end": "00001000",
                }
            )
        return cls.env["stock.picking.type"].create(vals)

    @classmethod
    def _create_picking(cls, picking_type):
        return cls.env["stock.picking"].create(
            {
                # el cliente no es decorativo: en autoimpreso el render cae al comprobante
                # estándar, y ese template no soporta un remito sin cliente (bug ajeno)
                "partner_id": cls.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )

    def _resolved_paperformat(self, res_ids):
        """El paperformat que el motor usaría para imprimir esas transferencias.

        Reproduce lo que hace el core en ``_run_wkhtmltopdf``, así el test recorre la cadena
        real: el override de ``_render_qweb_pdf_prepare_streams`` deja el dato en el contexto y
        ``get_paperformat`` lo lee de ahí."""
        resolved = []

        def capture(self_report, bodies, report_ref=False, **kwargs):
            resolved.append(self_report._get_report(report_ref).get_paperformat())
            return b"%PDF-1.4 fake"

        # force_report_rendering: sin eso, en tests Odoo devuelve el HTML y nunca llama a
        # wkhtmltopdf, que es justo el paso donde se resuelve el paperformat.
        with patch.object(type(self.env["ir.actions.report"]), "_run_wkhtmltopdf", capture):
            self.report.with_context(force_report_rendering=True)._render_qweb_pdf(self.report.report_name, res_ids)
        self.assertEqual(len(resolved), 1, "el render tendría que haber llamado a wkhtmltopdf una vez")
        return resolved[0]

    def test_own_paperformat_reaches_the_render(self):
        """En preimpreso con formato propio, el PDF se arma con ese formato y no con el del reporte.

        Es el test que importa: ``get_paperformat`` no recibe los registros, así que el dato solo
        llega si el override del render lo pone en el contexto."""
        self.assertEqual(self._resolved_paperformat(self.picking.ids), self.paperformat)

    def test_without_own_paperformat_keeps_the_report_one(self):
        """Sin formato propio no cambia nada: manda el del reporte (o el de la compañía)."""
        self.picking_type.l10n_ar_delivery_paperformat_id = False
        self.assertEqual(self._resolved_paperformat(self.picking.ids), self.report.get_paperformat())

    def test_autoprinted_ignores_own_paperformat(self):
        """En autoimpreso el remito sale sobre papel en blanco: las medidas de la base son las
        correctas, así que el formato del tipo de operación no se aplica aunque esté cargado."""
        autoprinted_type = self._create_picking_type("autoprinted", "TESTAUTPF")
        autoprinted_type.l10n_ar_delivery_report_view_id = self.custom_view
        autoprinted_type.l10n_ar_delivery_paperformat_id = self.paperformat
        picking = self._create_picking(autoprinted_type)
        self.assertFalse(picking._l10n_ar_preprinted_paperformat())
        self.assertEqual(self._resolved_paperformat(picking.ids), self.report.get_paperformat())

    def test_mixed_geometries_are_refused(self):
        """Una tanda con geometrías distintas no se imprime: wkhtmltopdf recibe un solo juego de
        medidas por corrida, así que unas saldrían bien y otras no. En papel preimpreso eso es
        papel numerado arruinado, así que el error es preferible al PDF."""
        other_type = self._create_picking_type("preprinted", "TESTPREPF2")
        other_type.l10n_ar_delivery_report_view_id = self.custom_view
        other_picking = self._create_picking(other_type)
        with self.assertRaises(UserError):
            self.report._l10n_ar_preprinted_paperformat((self.picking + other_picking).ids)

    def test_same_geometry_in_one_batch_is_allowed(self):
        """Varias transferencias del mismo talonario se imprimen juntas, que es el caso normal."""
        other_type = self._create_picking_type("preprinted", "TESTPREPF3")
        other_type.l10n_ar_delivery_paperformat_id = self.paperformat
        other_picking = self._create_picking(other_type)
        self.assertEqual(
            self.report._l10n_ar_preprinted_paperformat((self.picking + other_picking).ids),
            self.paperformat,
        )

    def test_other_reports_are_untouched(self):
        """El mecanismo es del remito: otro reporte de transferencias sigue con su propio formato."""
        operations_report = self.env.ref("stock.action_report_picking")
        self.assertFalse(operations_report._l10n_ar_preprinted_paperformat(self.picking.ids))
