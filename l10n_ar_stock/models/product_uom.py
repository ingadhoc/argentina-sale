# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from openerp import fields, models


class ProductUom(models.Model):
    _inherit = 'product.uom'

    arba_code = fields.Char(
    )
