##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    l10n_ar_delivery_guide_number = fields.Char(
        compute="_compute_l10n_ar_delivery_guide_number",
        inverse="_inverse_l10n_ar_delivery_guide_number",
        string="Delivery Guide No.",
    )
    country_code = fields.Char(related="company_id.account_fiscal_country_id.code")
    l10n_ar_allow_generate_delivery_guide = fields.Boolean(
        compute="_compute_l10n_ar_delivery_guide_flags",
    )

    @api.depends("state", "l10n_ar_delivery_guide_number", "picking_type_id.l10n_ar_document_type_id")
    def _compute_l10n_ar_delivery_guide_flags(self):
        """
        Compute flags for allowing delivery guide generation and sending.
        - Generation allowed if: state is 'done', document type exists, and no guide number.
        - Send allowed if: guide number exists.
        """
        for batch in self:
            has_doc_type = bool(batch.picking_type_id.l10n_ar_document_type_id)
            batch.l10n_ar_allow_generate_delivery_guide = (
                batch.state == "done" and has_doc_type and not batch.l10n_ar_delivery_guide_number
            )

    @api.depends("picking_ids.l10n_ar_delivery_guide_number")
    def _compute_l10n_ar_delivery_guide_number(self):
        for batch in self:
            delivery_guide_numbers = list(
                set(batch.picking_ids.filtered("l10n_ar_delivery_guide_number").mapped("l10n_ar_delivery_guide_number"))
            )
            batch.l10n_ar_delivery_guide_number = ", ".join(delivery_guide_numbers)

    def _inverse_l10n_ar_delivery_guide_number(self):
        for batch in self:
            batch.picking_ids.write({"l10n_ar_delivery_guide_number": batch.l10n_ar_delivery_guide_number})

    def l10n_ar_action_create_delivery_guide(self):
        """
        Assign delivery guid info to related pickings
        """
        for batch in self:
            if not batch.l10n_ar_delivery_guide_number:
                batch.picking_ids[:1].l10n_ar_action_create_delivery_guide()
                batch.picking_ids[1:].write(
                    {
                        "l10n_ar_delivery_guide_number": batch.picking_ids[0].l10n_ar_delivery_guide_number,
                        "l10n_ar_cai_data": batch.picking_ids[0].l10n_ar_cai_data,
                    }
                )

    @api.onchange("l10n_ar_delivery_guide_number")
    def _format_document_number(self):
        if self.l10n_ar_delivery_guide_number:
            if "," in self.l10n_ar_delivery_guide_number:
                docs = self.l10n_ar_delivery_guide_number.split(",")
            else:
                docs = [self.l10n_ar_delivery_guide_number]
            l10n_ar_delivery_guide_numbers = []
            for doc in docs:
                l10n_ar_delivery_guide_numbers.append(self.env.ref("l10n_ar.dc_r_r")._format_document_number(doc))
            self.l10n_ar_delivery_guide_number = ",".join(l10n_ar_delivery_guide_numbers)
