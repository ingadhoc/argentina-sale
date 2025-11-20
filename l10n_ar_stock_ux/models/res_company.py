import logging
import warnings

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
