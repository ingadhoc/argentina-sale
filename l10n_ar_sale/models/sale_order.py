##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
# from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    report_amount_tax = fields.Monetary(
        string='Tax',
        compute='_compute_report_amount_and_taxes'
    )
    report_amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_report_amount_and_taxes'
    )
    # report_tax_line_ids = fields.One2many(
    #     compute="_compute_report_amount_and_taxes",
    #     comodel_name='account.invoice.tax',
    #     string='Taxes'
    # )
    vat_discriminated = fields.Boolean(
        compute='_compute_vat_discriminated')

    sale_checkbook_id = fields.Many2one(
        'sale.checkbook',
    )

    @api.depends(
        'partner_id',
        'partner_id.afip_responsability_type_id',
        'company_id',
        'company_id.partner_id.afip_responsability_type_id',)
    def _compute_vat_discriminated(self):
        for rec in self:
            # si tiene checkbook y discrimna en funcion al partner pero
            # no tiene responsabilidad seteada, dejamos comportamiento nativo
            # de odoo de discriminar impuestos
            if rec.sale_checkbook_id:
                discriminate_taxes = rec.sale_checkbook_id.discriminate_taxes
                if discriminate_taxes == 'yes':
                    vat_discriminated = True
                elif discriminate_taxes == 'no':
                    vat_discriminated = False
                else:
                    letters = rec.env['account.journal']._get_journal_letter(
                        'sale', rec.company_id,
                        rec.partner_id.commercial_partner_id)
                    vat_discriminated = \
                        letters and not letters[0].taxes_included or True
                rec.vat_discriminated = vat_discriminated
                continue

            # dejamos esto por compatibilidad hacia atras sin sale.checkbook
            vat_discriminated = True
            company_vat_type = rec.company_id.sale_allow_vat_no_discrimination
            if company_vat_type and company_vat_type != 'discriminate_default':
                letters = rec.env[
                    'account.journal']._get_journal_letter(
                        'sale', rec.company_id,
                        rec.partner_id.commercial_partner_id)
                if letters:
                    vat_discriminated = not letters[0].taxes_included
                # if no responsability or no letters
                if not letters and \
                        company_vat_type == 'no_discriminate_default':
                    vat_discriminated = False
            rec.vat_discriminated = vat_discriminated

    @api.depends(
        'amount_untaxed', 'amount_tax', 'vat_discriminated')
    def _compute_report_amount_and_taxes(self):
        """
        Similar a account_document intoive pero por ahora incluimos o no todos
        los impuestos
        """
        for order in self:
            taxes_included = not order.vat_discriminated
            if not taxes_included:
                report_amount_tax = order.amount_tax
                report_amount_untaxed = order.amount_untaxed
                # not_included_taxes = order.order_line.mapped('tax_id')
            else:
                # not_included_taxes = False
                report_amount_tax = False
                report_amount_untaxed = order.amount_total
            #     not_included_taxes = (
            #         order.tax_line_ids - included_taxes)
            #     report_amount_tax = sum(not_included_taxes.mapped('amount'))
            #     report_amount_untaxed = order.amount_untaxed + sum(
            #         included_taxes.mapped('amount'))
            order.report_amount_tax = report_amount_tax
            order.report_amount_untaxed = report_amount_untaxed
            # order.report_tax_line_ids = not_included_taxes

    @api.onchange('company_id')
    def set_sale_checkbook(self):
        if self.company_id:
            self.sale_checkbook_id = self.env['sale.checkbook'].search(
                [('company_id', 'in', [self.company_id.id, False])], limit=1)
        else:
            self.sale_checkbook_id = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New') and \
                vals.get('sale_checkbook_id'):
            vals['name'] = self.env['sale.checkbook'].browse(
                vals.get('sale_checkbook_id')).sequence_id._next() or _('New')
        return super(SaleOrder, self).create(vals)
