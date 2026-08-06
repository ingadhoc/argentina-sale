##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models
from odoo.fields import Command


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _l10n_ar_tax_ids_from_commands(self, commands):
        """Devuelve los ids de impuestos que resultan de una lista de comandos x2many.

        Resolvemos los comandos en lugar de buscar uno en particular para no depender de
        cómo el estándar arma el valor de tax_ids (hoy CLEAR + LINK, podría ser SET).
        """
        tax_ids = set()
        for command in commands or []:
            code = command[0]
            if code == Command.SET:
                tax_ids = set(command[2] or [])
            elif code == Command.LINK:
                tax_ids.add(command[1])
            elif code == Command.UNLINK:
                tax_ids.discard(command[1])
            elif code == Command.CLEAR:
                tax_ids.clear()
        return tax_ids

    def _get_reward_values_free_shipping(self, reward, coupon, **kwargs):
        """El módulo sale_loyalty_delivery arma la línea de recompensa de envío gratis
        heredando los impuestos de la línea de flete del pedido, porque asume que el envío
        gratis descuenta un flete ya cargado por un transportista.

        Cuando el envío gratis se usa como promoción (por ejemplo por dominio de provincia)
        sobre un pedido sin transportista, no hay línea de flete de la cual heredar el IVA:
        la línea de recompensa nace sin impuestos y check_vat_tax (l10n_ar_sale) la rechaza.

        En ese caso tomamos el IVA del propio producto de la recompensa, tal como se
        obtendría agregando la línea a mano, y si ese producto no tiene impuestos (loyalty
        lo crea sin tomar los de la compañía) caemos al impuesto de venta por defecto de la
        compañía. La línea nace en 0 igual que en el comportamiento estándar y se recalcula
        cuando se elige el transportista, así que los importes del pedido no cambian.
        """
        res = super()._get_reward_values_free_shipping(reward, coupon, **kwargs)
        if not (self.company_id.country_id == self.env.ref("base.ar") and self.company_id.l10n_ar_company_requires_vat):
            return res
        for vals in res:
            if self._l10n_ar_tax_ids_from_commands(vals.get("tax_ids")):
                continue
            taxes = reward.discount_line_product_id.taxes_id or self.company_id.account_sale_tax_id
            taxes = self.fiscal_position_id.map_tax(taxes._filter_taxes_by_company(self.company_id))
            vals["tax_ids"] = [Command.clear()] + [Command.link(tax.id) for tax in taxes]
        return res
