##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    arba_code = fields.Char()

    @api.constrains("arba_code")
    def check_arba_code(self):
        for rec in self.filtered("arba_code"):
            if len(rec.arba_code) != 6 or not rec.arba_code.isdigit():
                raise ValidationError(self.env._("The ARBA nomenclature code must be exactly 6 numeric digits"))
