import math

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_ar_is_preprinted = fields.Boolean(
        related="picking_type_id.l10n_ar_is_preprinted",
    )

    def _l10n_ar_get_voucher_count(self):
        """Cantidad de comprobantes preimpresos (hojas) que consume la entrega.

        Cada hoja preimpresa trae su propio número; una entrega con más renglones de los que
        entran en una hoja consume varios números. Se calcula como el techo de
        (renglones a imprimir / renglones por hoja del tipo de operación). Si no se configuró
        ``l10n_ar_lines_per_voucher``, la entrega consume un único número.
        """
        self.ensure_one()
        lines_per_voucher = self.picking_type_id.l10n_ar_lines_per_voucher
        line_count = len(self.move_ids.filtered(lambda m: m.product_uom_qty))
        if not lines_per_voucher or not line_count:
            return 1
        return math.ceil(line_count / lines_per_voucher)

    def l10n_ar_action_create_delivery_guide(self):
        """En remitos preimpresos numeramos según las hojas consumidas (varios números
        separados por coma) y sin datos de CAI (el CAI viene impreso en el papel). En
        autoimpresos se delega al flujo estándar de Odoo (un número + datos de CAI)."""
        self.ensure_one()
        if self.l10n_ar_is_preprinted:
            if not self.l10n_ar_delivery_guide_number:
                picking_type = self.picking_type_id
                picking_type._ensure_l10n_ar_stock_sequence()
                count = self._l10n_ar_get_voucher_count()
                numbers = [picking_type.l10n_ar_sequence_id.next_by_id() for __ in range(count)]
                self.l10n_ar_delivery_guide_number = ",".join(numbers)
                # guardamos solo el tipo de documento; el CAI no aplica (viene preimpreso)
                self.l10n_ar_cai_data = {
                    "document_type_id": picking_type.l10n_ar_document_type_id.id,
                }
            return
        return super().l10n_ar_action_create_delivery_guide()
