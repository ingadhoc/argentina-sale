##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_allow_vat_no_discrimination = fields.Selection([
        ('discriminate', 'No, Always Discriminate'),
        ('no_discriminate_default', 'Yes, No Discriminate Default'),
        ('discriminate_default', 'Yes, Discriminate Default')
    ],
        'Sale Allow VAT no discrimination?',
        default='discriminate_default',
        help="Definie behaviour on sales orders and quoatations reports. "
        "Discrimination or not will depend in partner and company "
        "responsability and AFIP letters setup:"
        "\n* If No, Always Discriminate, then VAT will be discriminated like "
        "always in odoo"
        "\n* If Yes, No Discriminate Default, if no match found it won't "
        "discriminate by default"
        "\n* If Yes, Discriminate Default, if no match found it would "
        "discriminate by default"
    )
