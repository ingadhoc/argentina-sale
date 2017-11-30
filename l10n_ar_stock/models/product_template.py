# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    arba_code = fields.Char(
    )

    @api.multi
    @api.constrains('arba_code')
    def check_arba_code(self):
        for rec in self.filtered('arba_code'):
            if len(rec.arba_code) != 6 or not rec.arba_code.isdigit():
                raise UserError(_(
                    'El código según nomenclador de arba debe ser de 6 dígitos'
                    ' numéricos'))
