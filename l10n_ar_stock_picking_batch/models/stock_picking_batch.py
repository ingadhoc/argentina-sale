##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    # ── Argentine report fields ──────────────────────────────────────────────
    # Delegate to the first picking that has CAI/delivery-guide data.
    # All pickings in a batch share the same delivery guide (see
    # l10n_ar_action_create_delivery_guide), so picking_ids[0] is enough.

    l10n_ar_cai_data = fields.Json(
        compute="_compute_l10n_ar_report_fields",
        string="CAI Data",
    )
    document_type_id = fields.Many2one(
        comodel_name="l10n_latam.document.type",
        compute="_compute_l10n_ar_report_fields",
        string="Document Type (AR)",
    )
    l10n_ar_cai_expiration_date = fields.Date(
        compute="_compute_l10n_ar_report_fields",
        string="CAI Expiration Date",
    )
    l10n_ar_afip_barcode = fields.Char(
        compute="_compute_l10n_ar_report_fields",
        string="AFIP Barcode",
    )
    cot = fields.Char(
        compute="_compute_l10n_ar_report_fields",
        string="COT",
    )

    @api.depends(
        "picking_ids.l10n_ar_cai_data",
        "picking_ids.cot",
        "picking_ids.l10n_ar_afip_barcode",
        "picking_ids.l10n_ar_delivery_guide_number",
    )
    def _compute_l10n_ar_report_fields(self):
        for batch in self:
            # Take data from the first picking that has a delivery guide assigned
            ref_picking = batch.picking_ids.filtered("l10n_ar_delivery_guide_number")[:1]
            if ref_picking:
                batch.l10n_ar_cai_data = ref_picking.l10n_ar_cai_data
                batch.document_type_id = ref_picking.document_type_id
                batch.l10n_ar_cai_expiration_date = ref_picking.l10n_ar_cai_expiration_date
                batch.l10n_ar_afip_barcode = ref_picking.l10n_ar_afip_barcode
                batch.cot = ref_picking.cot
            else:
                batch.l10n_ar_cai_data = False
                batch.document_type_id = False
                batch.l10n_ar_cai_expiration_date = False
                batch.l10n_ar_afip_barcode = False
                batch.cot = False

    # ────────────────────────────────────────────────────────────────────────

    l10n_ar_delivery_guide_number = fields.Char(
        compute="_compute_l10n_ar_delivery_guide_number",
        inverse="_inverse_l10n_ar_delivery_guide_number",
        string="Delivery Guide No.",
    )
    country_code = fields.Char(related="company_id.account_fiscal_country_id.code")
    l10n_ar_allow_generate_delivery_guide = fields.Boolean(
        compute="_compute_l10n_ar_delivery_guide_flags",
    )
    automatic_declare_value = fields.Boolean(
        related="picking_type_id.automatic_declare_value",
    )
    declared_value = fields.Float(
        digits="Account",
        compute="_compute_declared_value",
        store=True,
        readonly=False,
    )

    @api.depends("picking_type_id.automatic_declare_value", "picking_ids.declared_value")
    def _compute_declared_value(self):
        for batch in self:
            batch.declared_value = sum(batch.picking_ids.mapped("declared_value"))

    def _get_name_delivery_report(self, report_xml_id):
        """Analogous to StockPicking._get_name_delivery_report in l10n_ar_stock_ux.
        Returns the Argentine batch report when the company is AR and a delivery
        guide number has been assigned; otherwise falls back to the generic report.
        """
        self.ensure_one()
        if self.company_id.country_id.code == "AR" and self.l10n_ar_delivery_guide_number:
            return "l10n_ar_stock_picking_batch.report_batch_delivery_document"
        return report_xml_id

    @api.depends("state", "l10n_ar_delivery_guide_number", "picking_type_id.l10n_ar_document_type_id")
    def _compute_l10n_ar_delivery_guide_flags(self):
        """
        Generation allowed if: state is 'done', document type exists, and no guide number yet.
        """
        for batch in self:
            has_doc_type = bool(batch.picking_type_id.l10n_ar_document_type_id)
            batch.l10n_ar_allow_generate_delivery_guide = (
                batch.state == "done" and has_doc_type and not batch.l10n_ar_delivery_guide_number
            )

    @api.depends("picking_ids.l10n_ar_delivery_guide_number")
    def _compute_l10n_ar_delivery_guide_number(self):
        for batch in self:
            delivery_guide_numbers = sorted(
                set(batch.picking_ids.filtered("l10n_ar_delivery_guide_number").mapped("l10n_ar_delivery_guide_number"))
            )
            batch.l10n_ar_delivery_guide_number = ", ".join(delivery_guide_numbers)

    def _inverse_l10n_ar_delivery_guide_number(self):
        for batch in self:
            pickings_to_update = batch.picking_ids.filtered(
                lambda p: p.l10n_ar_delivery_guide_number != batch.l10n_ar_delivery_guide_number
            )
            if pickings_to_update:
                pickings_to_update.write({"l10n_ar_delivery_guide_number": batch.l10n_ar_delivery_guide_number})

    def l10n_ar_action_create_delivery_guide(self):
        """
        Assign delivery guide info to related pickings
        """
        for batch in self:
            if not batch.partner_id:
                raise UserError(_("Para generar el remito debe definir un cliente o proveedor en el lote."))
            if not batch.l10n_ar_delivery_guide_number and batch.picking_ids:
                batch.picking_ids[:1].l10n_ar_action_create_delivery_guide()
                first_picking = batch.picking_ids[0]
                batch.picking_ids[1:].write(
                    {
                        "l10n_ar_delivery_guide_number": first_picking.l10n_ar_delivery_guide_number,
                        "l10n_ar_cai_data": first_picking.l10n_ar_cai_data,
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
                l10n_ar_delivery_guide_numbers.append(
                    self.env.ref("l10n_ar.dc_r_r")._format_document_number(doc.strip())
                )
            self.l10n_ar_delivery_guide_number = ",".join(l10n_ar_delivery_guide_numbers)
