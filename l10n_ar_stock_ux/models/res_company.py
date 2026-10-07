import logging
import warnings
import xml.etree.ElementTree as ET

import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

warnings.filterwarnings("ignore", category=DeprecationWarning)


_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    arba_cot = fields.Char(
        "Clave COT",
        help="Clave para generación de remito electŕonico",
    )

    @api.model
    def _get_arba_cot_login_url(self, environment_type=False):
        if not environment_type:
            environment_type = self._get_environment_type()
        _logger.info("Getting connection to ARBA on %s mode" % environment_type)
        base_url = "https://cot.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"
        if environment_type != "production":
            base_url = base_url.replace("cot.arba.gov.ar", "cot.test.arba.gov.ar")
        return base_url

    def _get_arba_cot_request_data(self):
        self.ensure_one()

        if not self.arba_cot:
            raise UserError(self.env._("You must configure ARBA COT on company %s", self.name))
        user = self.partner_id.ensure_vat()
        return {
            "Usuario": user,
            "Password": self.arba_cot,
        }

    def _arba_cot_check_credentials(self):
        """Check the COT credentials (CUIT and key) against the ARBA environment of this database.

        ARBA validates user and key before the file, so an empty file with an
        invalid name answers error 10 when the key is right and error 02 when
        it is wrong. Return the ARBA error code, the environment and the message.
        """
        self.ensure_one()
        environment_type = self._get_environment_type()
        login_url = self._get_arba_cot_login_url(environment_type)
        request_data = self._get_arba_cot_request_data()
        timeout = int(self.env["ir.config_parameter"].sudo().get_param("l10n_ar_stock_ux.arba_cot_timeout", default=40))
        try:
            res = requests.post(
                login_url,
                data=request_data,
                files={"file": ("test.txt", b"", "text/plain")},
                timeout=timeout,
            )
            root = ET.fromstring(res.content)
        except (requests.exceptions.RequestException, ET.ParseError) as error:
            raise UserError(self.env._("Could not connect to ARBA COT: %s", error)) from error
        code = root.findtext(".//codigoError")
        if not code:
            raise UserError(
                self.env._(
                    "Unexpected ARBA COT response. Status: %(status)s. Message: %(msg)s",
                    status=res.status_code,
                    msg=res.text[:500],
                )
            )
        message = root.findtext(".//mensajeError") or ""
        return code, environment_type, f"{message} ({code})"
