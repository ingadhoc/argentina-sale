##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _load(self, template_code, company, install_demo, force_create=True):
        if template_code in ("ar_base", "ar_ex", "ar_ri"):
            self.generate_stock_book(company)
        return super(AccountChartTemplate, self)._load(template_code, company, install_demo, force_create)

    @api.model
    def generate_stock_book(self, company):
        book_vals = self._prepare_all_book_data(company)
        self.check_created_book(book_vals, company)
        return True

    @api.model
    def check_created_book(self, book_vals, company):
        """
        This method used for checking new book already created or not.
        If not then create new book.
        """
        book = self.env["stock.book"].search([("name", "=", book_vals["name"]), ("company_id", "=", company.id)])
        if not book:
            book.sudo().create(book_vals)
        return True

    @api.model
    def _prepare_all_book_data(self, company):
        name = "Talonario (%s)" % (company.name)
        sequence_id = (
            self.env["ir.sequence"]
            .sudo()
            .create(
                {
                    "name": name,
                    "code": "stock.voucher",
                    "implementation": "no_gap",
                    "prefix": "000X-",
                    "padding": 8,
                    "number_increment": 1,
                    "company_id": company.id,
                }
            )
            .id
        )
        vals = {
            "name": name,
            "sequence_id": sequence_id,
            "lines_per_voucher": 0,
            "company_id": company.id,
        }
        return vals
