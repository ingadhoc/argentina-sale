##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _set_reversed_entry(self, credit_note):
        """Cuando una NC se genera desde la orden de venta, el core solo la vincula con su
        factura de origen si _refunds_origin_required(), que en AR es False. Sin ese vinculo
        el comprobante sale sin ninguna referencia a la factura que le dio origen, asi que
        al menos la dejamos en el campo Referencia."""
        res = super()._set_reversed_entry(credit_note)
        if (
            len(credit_note) == 1
            and credit_note.move_type == "out_refund"
            and credit_note.country_code == "AR"
            and not credit_note.ref
            and not credit_note.reversed_entry_id
        ):
            # a diferencia del core, alcanza con que compartan alguna linea de la orden:
            # asi tambien cubrimos el caso de una orden facturada en varias facturas
            origin_invoices = self.filtered(
                lambda inv: inv.move_type == "out_invoice"
                and credit_note.invoice_line_ids.sale_line_ids & inv.invoice_line_ids.sale_line_ids
            )
            if origin_invoices:
                credit_note.ref = ", ".join(sorted(origin_invoices.mapped("name")))
        return res
