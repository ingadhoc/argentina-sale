import math

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _l10n_ar_preprinted_aeroo_template(self):
        """Plantilla .odt con la que hay que imprimir este remito, o False si no hay ninguna y el
        comprobante sale por el camino qweb de siempre. Pedimos también el modo preimpreso: una
        plantilla cargada en un tipo autoimpreso no aplica, porque ahí Odoo imprime el comprobante
        completo (encabezado, número y CAI) y la plantilla del talonario no lo trae."""
        self.ensure_one()
        if self.l10n_ar_voucher_print_mode != "preprinted":
            return False
        return self.picking_type_id.l10n_ar_preprinted_template or False

    def _l10n_ar_preprinted_line_count(self):
        """Renglones de producto del comprobante. Es la misma cuenta que hace el comprobante de
        entrega de Odoo: antes de validar, los movimientos con cantidad pedida; después, un renglón
        por movimiento de detalle cuando se imprimen series y los renglones agregados por producto
        cuando no. Los títulos de sección de paquete no se cuentan: son del layout, no renglones de
        producto."""
        self.ensure_one()
        if self.state != "done":
            return len(self.move_ids.filtered(lambda m: m.product_uom_qty))
        move_lines = self.move_ids.move_line_ids
        if move_lines.lot_id and self.env.user.has_group("stock.group_lot_on_delivery_slip"):
            return len(move_lines)
        return len(move_lines._get_aggregated_product_quantities())

    def _l10n_ar_count_preprinted_sheets(self):
        """Con plantilla .odt las hojas no se pueden contar renderizando: la paginación la decide
        LibreOffice sobre la plantilla del cliente, y la marca invisible con la que el comprobante
        qweb reconoce las hojas con productos no existe ahí. El talonario preimpreso trae una
        cantidad fija de renglones por hoja, así que las hojas se calculan a partir de eso, que
        además es el mismo criterio con el que la imprenta armó el papel."""
        self.ensure_one()
        if not self._l10n_ar_preprinted_aeroo_template():
            return super()._l10n_ar_count_preprinted_sheets()
        lines_per_sheet = self.picking_type_id.l10n_ar_preprinted_lines_per_sheet
        return max(1, math.ceil(self._l10n_ar_preprinted_line_count() / lines_per_sheet))
