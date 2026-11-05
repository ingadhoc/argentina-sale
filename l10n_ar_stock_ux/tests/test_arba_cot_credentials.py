from unittest.mock import MagicMock, patch

import requests
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

    def _notification(self, content):
        settings = self.env["res.config.settings"].create({})
        response = MagicMock(status_code=200, content=content, text="")
        with patch("odoo.addons.l10n_ar_stock_ux.models.res_company.requests.post", return_value=response):
            return settings.action_arba_cot_check_credentials()["params"]

    def test_valid_key(self):
        result, post = self._check(ARBA_KEY_OK_RESPONSE)
        environment_type = self.company._get_environment_type()
        self.assertEqual(
            result,
            {
                "code": "10",
                "message": "El nombre del archivo recibido es incorrecto.",
                "environment_type": environment_type,
                "vat": "30714295698",
            },
        )
        self.assertEqual(post.call_args.args[0], self.company._get_arba_cot_login_url(environment_type))
        self.assertEqual(post.call_args.kwargs["data"], {"Usuario": "30714295698", "Password": "Test2017"})

    def test_invalid_key(self):
        result, _post = self._check(ARBA_KEY_INVALID_RESPONSE)
        self.assertEqual(result["code"], "02")
        self.assertEqual(result["message"], "El usuario ingresado y / o la contraseña son inválidos.")

    def test_unexpected_response(self):
        with self.assertRaisesRegex(UserError, "Unexpected ARBA COT response"):
            self._check(b"<html><body>Service unavailable</body></html>")

    def test_connection_error(self):
        errors = {
            "request": {"side_effect": requests.exceptions.ConnectionError("Connection refused")},
            "not xml": {"return_value": MagicMock(status_code=502, content=b"Bad gateway", text="")},
        }
        for case, mock_kwargs in errors.items():
            with (
                self.subTest(case=case),
                patch("odoo.addons.l10n_ar_stock_ux.models.res_company.requests.post", **mock_kwargs),
                self.assertRaisesRegex(UserError, "Could not connect to ARBA COT"),
            ):
                self.company._arba_cot_check_credentials()

    def test_settings_notification_valid(self):
        params = self._notification(ARBA_KEY_OK_RESPONSE)
        self.assertEqual(params["type"], "success")
        self.assertFalse(params["sticky"])
        self.assertIn(self.company.name, params["message"])
        self.assertIn("CUIT 30714295698", params["message"])
        self.assertIn("are valid", params["message"])
        self.assertNotIn("upper and lower case", params["message"])

    def test_settings_notification_invalid(self):
        params = self._notification(ARBA_KEY_INVALID_RESPONSE)
        self.assertEqual(params["type"], "danger")
        self.assertTrue(params["sticky"])
        self.assertIn(self.company.name, params["message"])
        self.assertIn("CUIT 30714295698", params["message"])
        self.assertIn("contraseña son inválidos. (02)", params["message"])
        self.assertIn("upper and lower case", params["message"])
