##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("type_id.discriminate_taxes")
    def _compute_vat_discriminated(self):
        recs = self.filtered(lambda x: x.type_id.discriminate_taxes in ["yes", "no"])
        for rec in recs:
            # si tiene checkbook y discrimna en funcion al partner pero no tiene responsabilidad seteada,
            # dejamos comportamiento nativo de odoo de discriminar impuestos
            discriminate_taxes = rec.type_id.discriminate_taxes
            if discriminate_taxes == "yes":
                rec.vat_discriminated = True
            else:
                rec.vat_discriminated = False
        return super(SaleOrder, self - recs)._compute_vat_discriminated()
