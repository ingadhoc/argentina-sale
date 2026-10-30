from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_arba_cot_enabled = fields.Boolean(
        "Usar COT de ARBA?",
        help="Permite generar el COT de arba una vez que se han asignado " "números de remitos en las entregas",
        implied_group="l10n_ar_stock_ux.arba_cot_enabled",
    )
    arba_cot = fields.Char(
        related="company_id.arba_cot",
        readonly=False,
    )

    def action_arba_cot_check_credentials(self):
        self.ensure_one()
        company = self.company_id
        code, environment_type, arba_message = company._arba_cot_check_credentials()
        is_valid = code == "10"
        environment = self.env._("production") if environment_type == "production" else self.env._("testing")
        values = {"company": company.name, "vat": company.partner_id.ensure_vat()}
        if is_valid:
            message = self.env._("The credentials of %(company)s (CUIT %(vat)s) are valid.", **values)
        else:
            message = self.env._(
                "Could not connect with the credentials of %(company)s (CUIT %(vat)s). ARBA answered: %(arba_message)s",
                arba_message=arba_message,
                **values,
            )
            if code == "02":
                message += " " + self.env._(
                    "Check that the CUIT is the one of the COT key and that the key matches upper and lower case."
                )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("ARBA COT - %s", environment),
                "message": message,
                "type": "success" if is_valid else "danger",
                "sticky": not is_valid,
            },
        }
