from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

ARBA_KEY_OK_RESPONSE = b"""<?xml version='1.0' encoding='ISO-8859-1'?><TBError>
  <tipoError>DATO</tipoError>
  <codigoError>10</codigoError>
  <mensajeError>El nombre del archivo recibido es incorrecto.</mensajeError>
</TBError>
"""

ARBA_KEY_INVALID_RESPONSE = """<?xml version='1.0' encoding='ISO-8859-1'?><TBError>
  <tipoError>DATO</tipoError>
  <codigoError>02</codigoError>
  <mensajeError>El usuario ingresado y / o la contraseña son inválidos.</mensajeError>
</TBError>
""".encode("iso-8859-1")


@tagged("post_install_l10n", "post_install", "-at_install")
class TestArbaCotCredentials(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.arba_cot = "Test2017"
        cls.company.partner_id.write(
            {
                "country_id": cls.env.ref("base.ar").id,
                "l10n_latam_identification_type_id": cls.env.ref("l10n_ar.it_cuit").id,
                "vat": "30714295698",
            }
        )

    def _check(self, content):
        response = MagicMock(status_code=200, content=content, text="")
        with patch("odoo.addons.l10n_ar_stock_ux.models.res_company.requests.post", return_value=response) as post:
            result = self.company._arba_cot_check_credentials()
        return result, post

    def test_valid_key(self):
        (code, environment_type, message), post = self._check(ARBA_KEY_OK_RESPONSE)
        self.assertEqual(code, "10")
        self.assertEqual(environment_type, self.company._get_environment_type())
        self.assertEqual(post.call_args.args[0], self.company._get_arba_cot_login_url(environment_type))
        self.assertEqual(post.call_args.kwargs["data"], {"Usuario": "30714295698", "Password": "Test2017"})
        self.assertIn("El nombre del archivo recibido es incorrecto. (10)", message)

    def test_invalid_key(self):
        (code, _environment_type, message), _post = self._check(ARBA_KEY_INVALID_RESPONSE)
        self.assertEqual(code, "02")
        self.assertIn("El usuario ingresado y / o la contraseña son inválidos. (02)", message)

    def test_unexpected_response(self):
        with self.assertRaisesRegex(UserError, "Unexpected ARBA COT response"):
            self._check(b"<html><body>Service unavailable</body></html>")

    def test_settings_notification(self):
        settings = self.env["res.config.settings"].create({})
        response = MagicMock(status_code=200, content=ARBA_KEY_INVALID_RESPONSE, text="")
        with patch("odoo.addons.l10n_ar_stock_ux.models.res_company.requests.post", return_value=response):
            action = settings.action_arba_cot_check_credentials()
        self.assertEqual(action["params"]["type"], "danger")
        self.assertIn(self.company.name, action["params"]["message"])
        self.assertIn("CUIT 30714295698", action["params"]["message"])
        self.assertIn("contraseña son inválidos. (02)", action["params"]["message"])
        self.assertIn("upper and lower case", action["params"]["message"])
