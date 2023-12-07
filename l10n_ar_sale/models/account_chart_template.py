##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api
from odoo.addons.account.models.chart_template import template

class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    def _load(self, template_code, company, install_demo):
        if company.country_id == self.env.ref('base.ar'):
            self.generate_sale_checkbook(company)
        return super(AccountChartTemplate, self)._load(template_code, company, install_demo)

    @api.model
    def generate_sale_checkbook(
            self, company):
        checkbook_vals = self._prepare_all_checkbook_data(company)
        self.check_created_checkbook(checkbook_vals, company)
        return True

    @api.model
    def check_created_checkbook(self, checkbook_vals, company):
        """
        This method used for checking new checkbook already created or not.
        If not then create new checkbook.
        """
        checkbook = self.env['sale.checkbook'].search([
            ('name', '=', checkbook_vals['name']),
            ('company_id', '=', company.id)])
        if not checkbook:
            checkbook.create(checkbook_vals)
        return True

    @api.model
    def _prepare_all_checkbook_data(self, company):
        vals = {
            'name': 'Talonario Ventas (%s)' % (company.name),
            'company_id': company.id,
        }
        return vals
