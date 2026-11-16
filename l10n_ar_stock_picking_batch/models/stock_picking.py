##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def l10n_ar_action_create_delivery_guide(self):
        """A picking in a batch with contact gets the single delivery guide of its batch,
        also from the list action that Odoo adds in 20.0."""
        if self.env.context.get("l10n_ar_picking_delivery_guide"):
            return super().l10n_ar_action_create_delivery_guide()
        in_partner_batch = self.filtered("batch_partner_id")
        if in_partner_batch.filtered(
            lambda p: p.l10n_ar_delivery_guide_number
            or p.state != "done"
            or not p.picking_type_id.l10n_ar_document_type_id
        ):
            # same error as Odoo for the transfers that cannot generate it
            return super().l10n_ar_action_create_delivery_guide()
        if in_partner_batch:
            in_partner_batch.batch_id.l10n_ar_action_create_delivery_guide()
        others = self - in_partner_batch
        if others:
            return super(StockPicking, others).l10n_ar_action_create_delivery_guide()

    def _l10n_ar_assign_delivery_guide_numbers(self):
        """Pickings of a batch with contact share a single automatic delivery guide."""
        in_partner_batch = self.filtered("batch_partner_id")
        super(StockPicking, self - in_partner_batch)._l10n_ar_assign_delivery_guide_numbers()
        for batch in in_partner_batch.batch_id:
            to_number = in_partner_batch.filtered(
                lambda p, batch=batch: p.batch_id == batch
                and p.picking_type_id.auto_assign_delivery_guide
                and p.picking_type_id.l10n_ar_document_type_id
                and not p.l10n_ar_delivery_guide_number
            )
            if not to_number:
                continue
            numbered = batch.picking_ids.filtered("l10n_ar_delivery_guide_number")[:1]
            if not numbered:
                numbered = to_number[:1]
                super(
                    StockPicking, numbered.with_context(l10n_ar_picking_delivery_guide=True)
                )._l10n_ar_assign_delivery_guide_numbers()
            (to_number - numbered).write(
                {
                    "l10n_ar_delivery_guide_number": numbered.l10n_ar_delivery_guide_number,
                    "l10n_ar_cai_data": numbered.l10n_ar_cai_data,
                }
            )
