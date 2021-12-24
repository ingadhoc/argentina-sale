##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class ProductUom(models.Model):
    _inherit = 'uom.uom'

    arba_code = fields.Char(
    )

    def action_arba_codes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': 'http://www.arba.gov.ar/bajadas/Fiscalizacion/Operativos/TransporteBienes/Documentacion/20080701-TB-TablasDeValidacion.pdf',
            'target': 'new'}
