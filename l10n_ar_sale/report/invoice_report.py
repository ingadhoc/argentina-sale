##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class AccountInvoiceReport(models.Model):
    """
    Este es un dummy depends para que si se actualza account_document no se
    rompa este reporte (porque sale agrega el campo team_id), hay que ver
    si en v10 ya lo mejoraron y no es necesario.
    En realidad esto debería ir en un modulo tipo "sale_document" o
    "sale_account_document" pero por practicidad lo hacemos aca
    """
    _inherit = 'account.invoice.report'
