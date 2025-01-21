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

    @api.depends(
        'partner_id.l10n_ar_afip_responsibility_type_id',
        'company_id.l10n_ar_company_requires_vat',)
    def _compute_vat_discriminated(self):
        for rec in self:
            rec.vat_discriminated = rec.company_id.l10n_ar_company_requires_vat and \
                rec.partner_id.l10n_ar_afip_responsibility_type_id.code in ['1'] or False

    def _compute_tax_totals(self):
        super()._compute_tax_totals()
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
            tax_group_vals = order.tax_totals['subtotals'][0]['tax_groups']
            # TODO revisar si es discriminar / no discrminar
            updated_tax_group_vals = list(filter(lambda x: x.get('id') not in to_remove_ids, tax_group_vals))
            order.tax_totals['subtotals'][0]['tax_groups'] = updated_tax_group_vals

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
