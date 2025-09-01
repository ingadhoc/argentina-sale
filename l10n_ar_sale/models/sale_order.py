##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    vat_discriminated = fields.Boolean(
        compute="_compute_vat_discriminated",
    )

    @api.depends(
        "partner_id.l10n_ar_afip_responsibility_type_id",
        "company_id.l10n_ar_company_requires_vat",
    )
    def _compute_vat_discriminated(self):
        for rec in self:
            rec.vat_discriminated = (
                rec.company_id.l10n_ar_company_requires_vat
                and rec.partner_id.l10n_ar_afip_responsibility_type_id.code in ["1"]
                or False
            )

    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        # discriminamos o no impuestos solo en pdf y portal. En backend siempre los mostramos. Para esto evaluamos:
        # commit_assetsbundle viene cuando sacamos pdf
        # portal_view lo mandamos cuando mostramos campo en portal
        report_or_portal_view = "commit_assetsbundle" in self.env.context or "from_portal_view" in self.env.context
        if not report_or_portal_view:
            return

        for order in self.filtered(lambda x: not x.vat_discriminated):
            tax_groups = order.order_line.mapped("tax_id.tax_group_id")
            if not tax_groups:
                continue
            to_remove_ids = tax_groups.filtered(lambda x: x.l10n_ar_vat_afip_code).ids
            tax_group_vals = order.tax_totals["subtotals"][0]["tax_groups"]
            # TODO revisar si es discriminar / no discrminar
            updated_tax_group_vals = list(filter(lambda x: x.get("id") not in to_remove_ids, tax_group_vals))
            order.tax_totals["subtotals"][0]["tax_groups"] = updated_tax_group_vals

    def _get_name_sale_report(self, report_xml_id):
        """Method similar to the '_get_name_invoice_report' of l10n_latam_invoice_document
        Basically it allows different localizations to define it's own report
        This method should actually go in a sale_ux module that later can be extended by different localizations
        Another option would be to use report_substitute module and setup a subsitution with a domain
        """
        self.ensure_one()
        if self.company_id.country_id.code == "AR":
            return "l10n_ar_sale.report_saleorder_document"
        return report_xml_id

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Por alguna razon cuando voy a crear la factura a traves de una devolucion, no me esta permitiendo crearla
        y validarla porque resulta el campo tipo de documento esta quedando vacio. Este campo se llena y computa
        automaticamente al generar al modificar el diaro de una factura.

        Si hacemos la prueba funcional desde la interfaz funciona, si intento importar la factura con el importador de
        Odoo funciona, pero si la voy a crear desde la devolucion inventario no se rellena dicho campo.

        Para solventar decimos si tenemos facturas que usan documentos y que no tienen un tipo de documento, intentamos
        computarlo y asignarlo, esto aplica para cuando generamos una factura desde una orden de venta o suscripcion"""
        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)

        # Intentamos Completar el dato tipo de documento si no seteado
        to_fix = invoices.filtered(lambda x: x.l10n_latam_use_documents and not x.l10n_latam_document_type_id)
        to_fix._compute_l10n_latam_available_document_types()
        if self.is_module_installed("sale_subscription_ux"):
            for invoice in invoices:
                so = invoice.invoice_line_ids[0].sale_line_ids.order_id or False
                if so and so.plan_id.bill_end_period:
                    new_period_start, new_period_stop, ratio, number_of_days = so.order_line[
                        0
                    ]._get_invoice_line_parameters()
                    invoice.l10n_ar_afip_service_start = new_period_start - so.plan_id.billing_period
                    invoice.l10n_ar_afip_service_end = new_period_stop - so.plan_id.billing_period

        return invoices

    def is_module_installed(self, module):
        module_installed = self.env["ir.module.module"].search(
            [
                ("name", "=", module),
                ("state", "=", "installed"),
            ]
        )
        return True if module_installed else False

    @api.onchange("date_order")
    def _l10n_ar_recompute_fiscal_position_taxes(self):
        """Recalculamos las percepciones si cambiamos la fecha de la orden de venta. Para ello nos basamos en los
        impuestos de la posicion fiscal, buscamos si hay impuestos existentes para los tax groups involucrados y los
        reemplazamos por los nuevos impuestos.
        """
        for rec in self.filtered(
            lambda x: x.fiscal_position_id.l10n_ar_tax_ids.filtered(lambda x: x.tax_type == "perception")
            and x.state not in ["cancel", "sale"]
        ):
            fp_tax_groups = rec.fiscal_position_id.l10n_ar_tax_ids.filtered(
                lambda x: x.tax_type == "perception"
            ).mapped("default_tax_id.tax_group_id")
            date = fields.Date.to_date(fields.Datetime.context_timestamp(rec, rec.date_order))
            new_taxes = rec.fiscal_position_id._l10n_ar_add_taxes(rec.partner_id, rec.company_id, date, "perception")
            for line in rec.order_line:
                to_unlink = line.tax_id.filtered(lambda x: x.tax_group_id in fp_tax_groups)
                if to_unlink._origin != new_taxes:
                    line.tax_id = [(3, tax.id) for tax in to_unlink] + [
                        (4, tax.id) for tax in new_taxes if tax not in line.tax_id
                    ]

    def copy(self, default=None):
        """Re computamos las percepciones al duplicar una venta porque puede ser que la orden venga de otro periodo
        o por alguna razón las percepciones hayan cambiado
        """
        recs = super().copy(default=default)
        recs._l10n_ar_recompute_fiscal_position_taxes()
        return recs
