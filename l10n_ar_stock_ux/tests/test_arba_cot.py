from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

ARBA_OK_RESPONSE = b"""<?xml version="1.0" encoding="ISO-8859-1"?>
<TBCOMM>
    <cuitEmpresa>30111111118</cuitEmpresa>
    <numeroComprobante>123456</numeroComprobante>
    <nombreArchivo>TB_30111111118_000000_20260924_000001.txt</nombreArchivo>
    <codigoIntegridad>abc123</codigoIntegridad>
    <validacionesRemitos class="list">
        <remito>
            <numeroUnico>000400000592</numeroUnico>
            <procesado>SI</procesado>
            <cot>9876543210</cot>
        </remito>
    </validacionesRemitos>
</TBCOMM>
"""

ARBA_ERROR_RESPONSE = b"""<?xml version="1.0" encoding="ISO-8859-1"?>
<TBCOMM>
    <validacionesRemitos class="list">
        <remito>
            <numeroUnico>000400000592</numeroUnico>
            <procesado>NO</procesado>
            <errores>
                <error>
                    <codigo>1/7</codigo>
                    <descripcion>El remito ya fue procesado con anterioridad</descripcion>
                </error>
            </errores>
        </remito>
    </validacionesRemitos>
</TBCOMM>
"""


@tagged("post_install_l10n", "post_install", "-at_install")
class TestArbaCotResponse(TransactionCase):
    def test_parse_successful_response(self):
        cot = self.env["stock.picking"]._parse_arba_response(ARBA_OK_RESPONSE)
        self.assertEqual(
            cot,
            {
                "procesado": "SI",
                "numeroUnico": "000400000592",
                "cot": "9876543210",
                "numeroComprobante": "123456",
                "codigoIntegridad": "abc123",
            },
        )

    def test_parse_error_response(self):
        with self.assertLogs("odoo.addons.l10n_ar_stock_ux.models.stock_picking", level="WARNING") as logs:
            with self.assertRaisesRegex(UserError, "1/7 El remito ya fue procesado con anterioridad"):
                self.env["stock.picking"]._parse_arba_response(ARBA_ERROR_RESPONSE)
        self.assertIn("ya fue procesado con anterioridad", logs.output[0])
