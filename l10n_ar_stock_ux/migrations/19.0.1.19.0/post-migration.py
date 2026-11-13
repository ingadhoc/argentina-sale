import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Set ARBA code 4 on the square meter.

    The data file pointed to an xmlid that does not exist in 19 and is noupdate, so the
    fixed record is not loaded again on existing databases. Only fills an empty code.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    uom = env.ref("uom.product_uom_square_meter", raise_if_not_found=False)
    if uom and not uom.arba_code:
        uom.arba_code = "4"
        _logger.info("ARBA code 4 set on uom %s", uom.id)
