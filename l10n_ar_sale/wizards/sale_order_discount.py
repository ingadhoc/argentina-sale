from odoo import Command, models


class SaleOrderDiscount(models.TransientModel):

    _inherit = 'sale.order.discount'

    def _prepare_discount_line_values(self, product, amount, taxes, description=None):
        """ Esta herencia lo hacemos para que funcione agregar un descuento, sin esto da el error que no
        puede crear la linea de venta porque le falta un impuesto de IVA. Siguiendo la misma logica de la opcion de
        descuentos por porcentaje, lo que hacemos es que obtenemos cual es el impuesto disponible en las otras lineas
        y de ahi replicamos y agregamos el mismo impuesto en la linea de descuento

        TODO Al migrar este modulo a version 18 quitar esta funcionalidad, porque ya el wizar lo tiene solucionado
        agregando el campo impuestos para que el usuario manualmente lo seleccione. """
        res = super()._prepare_discount_line_values(product, amount, taxes, description=description)
        if res.get('tax_id') == [Command.set([])]:
            if tax_ids := self.sale_order_id.order_line.tax_id.filtered(lambda t: t.tax_group_id.l10n_ar_vat_afip_code)[:1]:
                res['tax_id'] = [Command.set(tax_ids.ids)]

        return res
