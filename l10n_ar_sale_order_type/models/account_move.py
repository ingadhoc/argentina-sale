from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains("state", "l10n_latam_document_type_id")
    def _check_l10n_latam_documents(self):
        # EXTENDS l10n_latam_invoice_document
        if not self.partner_id.l10n_ar_afip_responsibility_type_id:
            raise ValidationError(_("The customer has not specified the field 'AFIP Responsibility'"))
        super()._check_l10n_latam_documents()
