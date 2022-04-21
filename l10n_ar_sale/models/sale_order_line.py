##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    report_price_unit = fields.Float(
        compute='_compute_report_prices_and_taxes',
        digits='Report Product Price',
    )
    price_unit_with_tax = fields.Float(
        compute='_compute_report_prices_and_taxes',
        digits='Product Price',
    )
    report_price_subtotal = fields.Monetary(
        compute='_compute_report_prices_and_taxes'
    )
    report_price_net = fields.Float(
        compute='_compute_report_prices_and_taxes',
        digits='Report Product Price',
    )
    report_tax_id = fields.One2many(
        compute="_compute_report_prices_and_taxes",
        comodel_name='account.tax',
    )

    vat_tax_id = fields.Many2one(
        'account.tax',
        compute='_compute_vat_tax_id',
    )
    report_price_reduce = fields.Monetary(
        compute='_compute_report_price_reduce'
    )

    @api.depends('price_unit', 'price_subtotal', 'order_id.vat_discriminated')
    def _compute_report_price_reduce(self):
        for line in self:
            price_type = line.price_subtotal \
                if line.order_id.vat_discriminated else line.price_total
            line.report_price_reduce = price_type / line.product_uom_qty \
                if line.product_uom_qty else 0.0

    @api.depends(
        'tax_id.tax_group_id.l10n_ar_vat_afip_code',
    )
    def _compute_vat_tax_id(self):
        for rec in self:
            vat_tax_id = rec.tax_id.filtered(lambda x: x.tax_group_id.l10n_ar_vat_afip_code)
            if len(vat_tax_id) > 1:
                raise UserError(_('Only one vat tax allowed per line'))
            rec.vat_tax_id = vat_tax_id

    @api.depends(
        'price_unit',
        'price_subtotal',
        'order_id.vat_discriminated'
    )
    def _compute_report_prices_and_taxes(self):
        for line in self:
            order = line.order_id
            taxes_included = not order.vat_discriminated
            price_unit = line.tax_id.with_context(round=False).compute_all(
                line.price_unit, order.currency_id, 1.0, line.product_id,
                order.partner_shipping_id)
            if not taxes_included:
                report_price_unit = price_unit['total_excluded']
                report_price_subtotal = line.price_subtotal
                not_included_taxes = line.tax_id
                report_price_net = report_price_unit * (
                    1 - (line.discount or 0.0) / 100.0)
            else:
                included_taxes = line.tax_id.filtered(lambda x: x.tax_group_id.l10n_ar_vat_afip_code)
                not_included_taxes = (
                    line.tax_id - included_taxes)
                report_price_unit = included_taxes.with_context(
                    round=False).compute_all(
                    line.price_unit, order.currency_id, 1.0, line.product_id,
                    order.partner_shipping_id)['total_included']
                report_price_net = report_price_unit * (
                    1 - (line.discount or 0.0) / 100.0)
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                report_price_subtotal = included_taxes.compute_all(
                    price, order.currency_id, line.product_uom_qty,
                    line.product_id, order.partner_shipping_id)['total_included']

            line.price_unit_with_tax = price_unit['total_included']
            line.report_price_subtotal = report_price_subtotal
            line.report_price_unit = report_price_unit
            line.report_price_net = report_price_net
            line.report_tax_id = not_included_taxes

    @api.model
    def create(self, vals):
        rec = super(SaleOrderLine, self).create(vals)
        rec.check_vat_tax()
        return rec

    def check_vat_tax(self):
        """For recs of argentinian companies with l10n_ar_company_requires_vat (that
        comes from the responsability), we ensure one and only one vat tax is
        configured
        TODO: we could also integrate with so_type invoice journal id or
        with sale_checkbook_id
        """
        # por ahora, para no romper el install de sale_timesheet lo
        # desactivamos en la instalacion
        if self.env.context.get('install_mode'):
            return True
        for rec in self.filtered(
                lambda x: not x.display_type and
                x.company_id.country_id == self.env.ref('base.ar') and
                x.company_id.l10n_ar_company_requires_vat):
            vat_taxes = rec.tax_id.filtered(
                lambda x: x.tax_group_id.l10n_ar_vat_afip_code)
            if len(vat_taxes) != 1:
                raise UserError(_(
                    'Debe haber un único impuesto del grupo de impuestos "IVA" por línea, agréguelo a "%s". '
                    'En caso de tenerlo, revise la configuración del impuesto, en opciones avanzadas, '
                    'en el campo correspondiente "Grupo de Impuestos".' % (
                        rec.product_id.name)))

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        # for performance we only check if tax or company is on vals
        if 'tax_id' in vals or 'company_id' in vals:
            self.check_vat_tax()
        return res

    @api.depends('order_id.date_order')
    def _compute_amount(self):
        """ Ver descripcion en modificacion en sale.order._amount_by_group
        """
        for line in self:
            date_order = line.order_id.date_order or fields.Date.context_today(line)
            line = line.with_context(invoice_date=date_order)
            super(SaleOrderLine, line)._compute_amount()
