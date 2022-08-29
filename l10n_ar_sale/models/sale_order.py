##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
import json
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    vat_discriminated = fields.Boolean(
        compute='_compute_vat_discriminated',
    )
    sale_checkbook_id = fields.Many2one(
        'sale.checkbook',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    )

    @api.depends(
        'partner_id.l10n_ar_afip_responsibility_type_id',
        'company_id.l10n_ar_company_requires_vat',)
    def _compute_vat_discriminated(self):
        for rec in self:
            # si tiene checkbook y discrimna en funcion al partner pero no tiene responsabilidad seteada,
            # dejamos comportamiento nativo de odoo de discriminar impuestos
            discriminate_taxes = rec.sale_checkbook_id.discriminate_taxes
            if discriminate_taxes == 'yes':
                vat_discriminated = True
            elif discriminate_taxes == 'no':
                vat_discriminated = False
            else:
                vat_discriminated = rec.company_id.l10n_ar_company_requires_vat and \
                    rec.partner_id.l10n_ar_afip_responsibility_type_id.code in ['1'] or False
            rec.vat_discriminated = vat_discriminated

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

    def _compute_tax_totals_json(self):
        # usamos mismo approach que teniamos para facturas en v13, es decir, con esto sabemos si se está solicitando el
        # json desde reporte o qweb y en esos casos vemos de incluir impuestos, pero en backend siempre discriminamos
        # eventualmente podemos usar mismo approach de facturas en v15 donde ya no se hace asi, si no que cambiamos
        # el reporte de facturas usando nuevo metodo _l10n_ar_get_invoice_totals_for_report
        report_or_portal_view = 'commit_assetsbundle' in self.env.context or \
            not self.env.context.get('params', {}).get('view_type') == 'form'
        if not report_or_portal_view:
            return super()._compute_tax_totals_json()
        for order in self:
            # Hacemos esto para disponer de fecha del pedido y cia para calcular
            # impuesto con código python (por ej. para ARBA).
            # lo correcto seria que esto este en un modulo que dependa de l10n_ar_account_withholding, pero queremos
            # evitar ese modulo adicional por ahora
            date_order = order.date_order or fields.Date.context_today(order)
            order = order.with_context(invoice_date=date_order)
            if order.vat_discriminated:
                super(SaleOrder, order)._compute_tax_totals_json()
            else:
                def compute_taxes(order_line):
                    price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                    order = order_line.order_id
                    return order_line.report_tax_id._origin.compute_all(price, order.currency_id, order_line.product_uom_qty, product=order_line.product_id, partner=order.partner_shipping_id)

                account_move = self.env['account.move']
                for order in self:
                    tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line, compute_taxes)
                    tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
                    order.tax_totals_json = json.dumps(tax_totals)

    def _get_name_sale_report(self, report_xml_id):
        """ Method similar to the '_get_name_invoice_report' of l10n_latam_invoice_document
        Basically it allows different localizations to define it's own report
        This method should actually go in a sale_ux module that later can be extended by different localizations
        Another option would be to use report_substitute module and setup a subsitution with a domain
        """
        self.ensure_one()
        if self.company_id.country_id.code == 'AR':
            return 'l10n_ar_sale.report_saleorder_document'
        return report_xml_id
