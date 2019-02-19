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

    report_price_unit = fields.Monetary(
        string='Unit Price',
        compute='_compute_report_prices_and_taxes'
    )
    price_unit_with_tax = fields.Monetary(
        string='Price Unit Price',
        compute='_compute_report_prices_and_taxes'
    )
    report_price_subtotal = fields.Monetary(
        string='Amount',
        compute='_compute_report_prices_and_taxes'
    )
    report_price_net = fields.Monetary(
        string='Net Amount',
        compute='_compute_report_prices_and_taxes'
    )
    report_tax_id = fields.One2many(
        compute="_compute_report_prices_and_taxes",
        comodel_name='account.tax',
        string='Taxes'
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

    @api.multi
    @api.depends(
        'tax_id.tax_group_id.type',
        'tax_id.tax_group_id.tax',
    )
    def _compute_vat_tax_id(self):
        for rec in self:
            vat_tax_id = rec.tax_id.filtered(lambda x: (
                x.tax_group_id.type == 'tax' and
                x.tax_group_id.tax == 'vat'))
            if len(vat_tax_id) > 1:
                raise UserError(_('Only one vat tax allowed per line'))
            rec.vat_tax_id = vat_tax_id

    @api.multi
    @api.depends(
        'price_unit',
        'price_subtotal',
        'order_id.vat_discriminated'
    )
    def _compute_report_prices_and_taxes(self):
        """
        Similar a account_document pero por ahora inluimos o no todos los
        impuestos
        """
        for line in self:
            order = line.order_id
            taxes_included = not order.vat_discriminated
            price_unit = line.tax_id.compute_all(
                line.price_unit, order.currency_id, 1.0, line.product_id,
                order.partner_id)
            if not taxes_included:
                report_price_unit = price_unit['total_excluded']
                report_price_subtotal = line.price_subtotal
                not_included_taxes = line.tax_id
                report_price_net = report_price_unit * (
                    1 - (line.discount or 0.0) / 100.0)
            else:
                included_taxes = line.tax_id
                not_included_taxes = (
                    line.tax_id - included_taxes)
                report_price_unit = included_taxes.compute_all(
                    line.price_unit, order.currency_id, 1.0, line.product_id,
                    order.partner_id)['total_included']
                report_price_net = report_price_unit * (
                    1 - (line.discount or 0.0) / 100.0)
                report_price_subtotal = (
                    report_price_net * line.product_uom_qty)

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

    @api.multi
    def check_vat_tax(self):
        """For recs of argentinian companies with company_requires_vat (that
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
                lambda x: x.company_id.localization == 'argentina' and
                x.company_id.company_requires_vat):
            vat_taxes = rec.tax_id.filtered(
                lambda x:
                x.tax_group_id.tax == 'vat' and x.tax_group_id.type == 'tax')
            if len(vat_taxes) != 1:
                raise UserError(_(
                    'Debe haber un y solo un impuestos de IVA por línea. '
                    'Verificar líneas con producto "%s"' % (
                        rec.product_id.name)))

    @api.multi
    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        # for performance we only check if tax or company is on vals
        if 'tax_id' in vals or 'company_id' in vals:
            self.check_vat_tax()
        return res
