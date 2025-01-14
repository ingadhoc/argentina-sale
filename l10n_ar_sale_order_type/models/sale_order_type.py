##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class SaleOrderType(models.Model):
    _inherit = "sale.order.type"

    discriminate_taxes = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
    )
    report_partner_id = fields.Many2one(
        "res.partner",
    )
    fiscal_country_codes = fields.Char(compute="_compute_fiscal_country_codes")

    @api.depends("company_id")
    @api.depends_context("allowed_company_ids")
    def _compute_fiscal_country_codes(self):
        for record in self:
            allowed_companies = record.company_id or self.env.companies
            record.fiscal_country_codes = ",".join(allowed_companies.mapped("account_fiscal_country_id.code"))
