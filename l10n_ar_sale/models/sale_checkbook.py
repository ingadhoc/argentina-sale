##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class SaleCheckbook(models.Model):
    _name = 'sale.checkbook'
    _description = 'sale.checkbook'
    _order = 'sequence'

    sequence = fields.Integer(
        help="Used to order the receiptbooks",
        default=10,
    )
    name = fields.Char(
        size=64,
        required=True,
        index=True,
    )
    discriminate_taxes = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
            ('according_to_partner', 'According to partner VAT responsibility')
        ],
        string='Discriminate taxes?',
        default='according_to_partner',
        required=True,
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        'Entry Sequence',
        help="This field contains the information related to the numbering "
        "of the receipt entries of this receiptbook.",
        copy=False,
        domain=[('code', '=', 'sale.order')],
        context={'default_code': 'sale.order'},
    )
    next_number = fields.Integer(
        related='sequence_id.number_next_actual',
        readonly=False,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        default=True,
    )
    report_partner_id = fields.Many2one(
        'res.partner',
    )

    @api.model
    def create(self, vals):
        rec = super(SaleCheckbook, self).create(vals)
        if not rec.sequence_id:
            rec.sequence_id = self.env['ir.sequence'].sudo().create({
                'name': rec.name,
                'code': 'sale.checkbook',
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'company_id': rec.company_id.id,
            }).id
        return rec
