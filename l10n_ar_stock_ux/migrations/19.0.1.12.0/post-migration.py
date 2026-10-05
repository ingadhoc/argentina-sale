import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Las copias del comprobante de entrega pasan del reporte al tipo de operación.

    Copiamos el valor que tenía el reporte a los tipos de operación de entregas e internos de
    compañías argentinas (los únicos donde se configura el campo, igual que el tipo de
    documento): así el remito sigue saliendo igual que antes de actualizar. Las bases sin
    copias en el reporte no cambian.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    report = env.ref("stock.action_report_delivery", raise_if_not_found=False)
    if not report or not report.l10n_ar_copies:
        return
    picking_types = (
        env["stock.picking.type"]
        .with_context(active_test=False)
        .search(
            [
                ("company_id.partner_id.country_id.code", "=", "AR"),
                ("code", "in", ("outgoing", "internal")),
                ("l10n_ar_copies", "=", False),
            ]
        )
    )
    picking_types.write({"l10n_ar_copies": report.l10n_ar_copies})
    _logger.info(
        "Delivery slip copies '%s' copied from the report to %s operation types",
        report.l10n_ar_copies,
        len(picking_types),
    )
