##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_report_price_unit(self, price=None):
        """Report unit price (with or without VAT), computed on the whole line so it is not
        rounded per unit: sale_product_uom_price converts it to the product unit."""
        self.ensure_one()
        price = self.price_unit if price is None else price
        order = self.order_id
        if order.vat_discriminated:
            taxes, key = self.tax_ids, "total_excluded"
        else:
            taxes, key = self.tax_ids.filtered(lambda x: x.tax_group_id.l10n_ar_vat_afip_code), "total_included"
        # The real quantity, so a fixed tax is applied once per unit and not once per line
        qty = self.product_uom_qty or 1.0
        res = taxes.with_context(round_base=False).compute_all(
            price, order.currency_id, qty, self.product_id, order.partner_shipping_id
        )
        return res[key] / qty

    @api.depends(
        "product_uom_qty",
        "tax_ids",
        "tax_ids.amount",
        "tax_ids.price_include_override",
        "tax_ids.tax_group_id.l10n_ar_vat_afip_code",
        "order_id.vat_discriminated",
        "order_id.currency_id",
        "order_id.partner_shipping_id",
    )
    def _compute_price_unit_product_uom(self):
        return super()._compute_price_unit_product_uom()
