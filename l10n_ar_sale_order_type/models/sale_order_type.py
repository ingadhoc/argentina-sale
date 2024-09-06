##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class SaleOrderType(models.Model):
    _inherit = "sale.order.type"

    sale_checkbook_id = fields.Many2one(
        'sale.checkbook',
        check_company=True,
        help='Si se define un checkbook se usara este para este type. Si no se define se dejara el que se tome por '
        'defecto.'
    )

    _sql_constraints = [
        ('only_one_sequence_on_sale_order',
          'CHECK((sequence_id IS null) OR (sale_checkbook_id IS null))',
            'No pueden estar seteada una secuencia de entrada y un talonario de ventas al mismo tiempo')
    ]
