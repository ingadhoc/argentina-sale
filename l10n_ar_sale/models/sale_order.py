##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from functools import partial
from odoo.tools.misc import formatLang
# from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    report_amount_untaxed = fields.Monetary(
        compute='_compute_report_report_amount_untaxed'
    )
    vat_discriminated = fields.Boolean(
        compute='_compute_vat_discriminated',
    )
    sale_checkbook_id = fields.Many2one(
        'sale.checkbook',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    )

    @api.depends(
        'partner_id',
        'partner_id.afip_responsability_type_id',
        'company_id',
        'company_id.partner_id.afip_responsability_type_id',)
    def _compute_vat_discriminated(self):
        use_sale_checkbook = self.env.user.has_group(
            'l10n_ar_sale.use_sale_checkbook')
        for rec in self:
            # si tiene checkbook y discrimna en funcion al partner pero
            # no tiene responsabilidad seteada, dejamos comportamiento nativo
            # de odoo de discriminar impuestos
            if use_sale_checkbook and rec.sale_checkbook_id:
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
                        not letters[0].taxes_included if letters else True
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

    @api.depends('amount_untaxed', 'vat_discriminated')
    def _compute_report_report_amount_untaxed(self):
        """
        Similar a account_document intoive pero por ahora incluimos o no todos
        los impuestos (TODO mejorar y solo incluir impuestos IVA)
        """
        for order in self:
            taxes_included = not order.vat_discriminated
            if not taxes_included:
                report_amount_untaxed = order.amount_untaxed
            else:
                report_amount_untaxed = order.amount_total - sum(
                    x[1] for x in order.amount_by_group)
            order.report_amount_untaxed = report_amount_untaxed

    @api.onchange('company_id')
    def set_sale_checkbook(self):
        if self.env.user.has_group('l10n_ar_sale.use_sale_checkbook') and \
           self.company_id:
            self.sale_checkbook_id = self.env['sale.checkbook'].search(
                [('company_id', 'in', [self.company_id.id, False])], limit=1)
        else:
            self.sale_checkbook_id = False

    @api.model
    def create(self, vals):
        if self.env.user.has_group('l10n_ar_sale.use_sale_checkbook') and \
            vals.get('name', _('New')) == _('New') and \
                vals.get('sale_checkbook_id'):
            sale_checkbook = self.env['sale.checkbook'].browse(
                vals.get('sale_checkbook_id'))
            vals['name'] = sale_checkbook.sequence_id and\
                sale_checkbook.sequence_id._next() or _('New')
        return super(SaleOrder, self).create(vals)

    def _amount_by_group(self):
        order_vat_not_discriminated = self.filtered(lambda x: not x.vat_discriminated)
        for order in order_vat_not_discriminated:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.report_tax_id.compute_all(
                    price_reduce, quantity=line.product_uom_qty, product=line.product_id,
                    partner=order.partner_shipping_id)['taxes']
                for tax in line.report_tax_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]
        super(SaleOrder, self - order_vat_not_discriminated)._amount_by_group()
