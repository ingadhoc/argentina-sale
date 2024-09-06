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
        compute="_compute_sale_checkbook",
        store=True,
        precompute=True,
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

    @api.depends('company_id')
    def _compute_sale_checkbook(self):
        for rec in self:
            if self.env.user.has_group('l10n_ar_sale.use_sale_checkbook'):
                # solo recalculamos si no habia checkbook o si la compañía no es compatible
                if not rec.sale_checkbook_id or (
                        rec.sale_checkbook_id.company_id and rec.sale_checkbook_id.company_id != rec.company_id):
                    rec.sale_checkbook_id = rec._get_sale_checkbook()
            else:
                rec.sale_checkbook_id = False

    def _get_sale_checkbook(self):
        return (
            self.env['ir.default'].sudo()._get('sale.order', 'sale_checkbook_id', company_id=self.company_id.id, user_id=self.env.user.id) or
            self.env['ir.default'].sudo()._get('sale.order', 'sale_checkbook_id', user_id=self.env.user.id) or
            self.env['ir.default'].sudo()._get('sale.order', 'sale_checkbook_id') or
            self.env['sale.checkbook'].search([('company_id', 'in', [self.company_id.id, False])], limit=1)
        )

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if self.env.user.has_group('l10n_ar_sale.use_sale_checkbook') and \
                val.get('name', _('New')) == _('New') and \
                    val.get('sale_checkbook_id'):
                sale_checkbook = self.env['sale.checkbook'].browse(
                    val.get('sale_checkbook_id'))
                val['name'] = sale_checkbook.sequence_id and\
                    sale_checkbook.sequence_id._next() or _('New')
        return super(SaleOrder, self).create(vals)

    def write(self, vals):
        """A sale checkbook could have a different order sequence, so we could
        need to change it accordingly"""
        if self.env.user.has_group('l10n_ar_sale.use_sale_checkbook') and vals.get('sale_checkbook_id'):
            sale_checkbook = self.env['sale.checkbook'].browse(vals['sale_checkbook_id'])
            if sale_checkbook.sequence_id:
                for record in self:
                    if record.sale_checkbook_id.sequence_id != sale_checkbook.sequence_id and record.state in {"draft", "sent"}:
                        record.name = sale_checkbook.sequence_id._next()
        return super().write(vals)

    def _compute_tax_totals(self):
        """ Mandamos en contexto el invoice_date para calculo de impuesto con partner aliquot
        ver módulo l10n_ar_account_withholding. """
        for rec in self:
            rec = rec.with_context(invoice_date=rec.date_order)
            super(SaleOrder, rec)._compute_tax_totals()
        # discriminamos o no impuestos solo en pdf y portal. En backend siempre los mostramos. Para esto evaluamos:
        # commit_assetsbundle viene cuando sacamos pdf
        # portal_view lo mandamos cuando mostramos campo en portal
        report_or_portal_view = 'commit_assetsbundle' in self.env.context or 'from_portal_view' in self.env.context
        if not report_or_portal_view:
            return

        for order in self.filtered(lambda x: not x.vat_discriminated):
            tax_groups = order.order_line.mapped('tax_id.tax_group_id')
            if not tax_groups:
                continue
            to_remove_ids = tax_groups.filtered(lambda x: x.l10n_ar_vat_afip_code).ids
            tax_group_name = list(order.tax_totals['groups_by_subtotal'].keys())[0]
            tax_group_vals = order.tax_totals['groups_by_subtotal'].get(tax_group_name)
            updated_tax_group_vals = list(filter(lambda x: x.get('tax_group_id') not in to_remove_ids, tax_group_vals))
            new_totals = order.tax_totals
            new_totals['groups_by_subtotal'].update({tax_group_name: updated_tax_group_vals})
            order.tax_totals = new_totals

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

    def _create_invoices(self, grouped=False, final=False, date=None):
        """ Por alguna razon cuando voy a crear la factura a traves de una devolucion, no me esta permitiendo crearla
        y validarla porque resulta el campo tipo de documento esta quedando vacio. Este campo se llena y computa
        automaticamente al generar al modificar el diaro de una factura.

        Si hacemos la prueba funcional desde la interfaz funciona, si intento importar la factura con el importador de
        Odoo funciona, pero si la voy a crear desde la devolucion inventario no se rellena dicho campo.

        Para solventar decimos si tenemos facturas que usan documentos y que no tienen un tipo de documento, intentamos
        computarlo y asignarlo, esto aplica para cuando generamos una factura desde una orden de venta o suscripcion """
        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)

        # Intentamos Completar el dato tipo de documento si no seteado 
        to_fix = invoices.filtered(lambda x: x.l10n_latam_use_documents and not x.l10n_latam_document_type_id)
        to_fix._compute_l10n_latam_available_document_types()
        return invoices

    def is_module_installed(self, module):
        module_installed = self.env['ir.module.module'].search([
            ('name', '=', module),
            ('state', '=', 'installed'),
        ])
        return True if module_installed else False
