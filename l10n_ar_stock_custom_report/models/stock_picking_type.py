from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_ar_delivery_report_view_id = fields.Many2one(
        "ir.ui.view",
        string="Plantilla del Remito",
        domain=[("type", "=", "qweb"), ("mode", "=", "primary")],
        ondelete="restrict",
        help="Vista QWeb propia con la que se imprime el remito de este tipo de operación, en lugar "
        "del comprobante estándar. Vacío, se usa el comprobante estándar y nada cambia.\n"
        "La plantilla la crea un consultor funcional o el propio cliente desde Ajustes > Técnico > "
        "Vistas, y hay dos formas de armarla según qué se necesite personalizar:\n"
        "* Formato: una plantilla desde cero, dibujada para la grilla del papel de la imprenta. "
        "Recibe la transferencia en la variable 'o' (y el tipo de copia en 'copy_type') y tiene que "
        'abrir con <t t-call="web.html_container"> igual que el comprobante estándar.\n'
        "* Campos: una vista de modo 'primary' que herede el comprobante estándar y le agregue los "
        "campos que falten. Conserva el formato nuestro, incluidos encabezado, número y CAI.\n"
        "En los dos casos la vista tiene que ser QWeb y de modo 'primary'.",
    )

    # === CONSTRAINT METHODS === #

    @api.constrains("l10n_ar_delivery_report_view_id")
    def _constrains_l10n_ar_delivery_report_view(self):
        """La plantilla tiene que ser una vista QWeb renderizable por sí misma. El domain del
        campo ya lo pide, pero el modo también puede setearse por import / data / ORM, donde el
        domain no aplica.

        El chequeo de 'primary' no es cosmético: una vista de modo 'extension' no tiene arch
        renderizable propio — es un diff de xpaths — así que el t-call del comprobante imprimiría
        los nodos del diff sueltos en vez del remito. Una vista 'primary' sí, tenga o no
        inherit_id: cuando lo tiene, Odoo sube por la herencia y aplica el diff sobre el arch del
        padre (ir.ui.view._get_combined_archs)."""
        for picking_type in self.filtered("l10n_ar_delivery_report_view_id"):
            view = picking_type.l10n_ar_delivery_report_view_id
            if view.type != "qweb" or view.mode != "primary":
                raise ValidationError(
                    _(
                        "La plantilla del remito de %(picking_type)s tiene que ser una vista QWeb"
                        " de modo 'primary', y %(view)s es de tipo %(type)s y modo %(mode)s.\n"
                        "Cree la plantilla desde Ajustes > Técnico > Vistas, con un <t t-name>"
                        " propio o heredando el comprobante estándar en modo 'primary'.",
                        picking_type=picking_type.display_name,
                        view=view.display_name,
                        type=view.type,
                        mode=view.mode,
                    )
                )
