from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_ar_voucher_print_mode = fields.Selection(
        selection=[
            ("autoprinted", "Autoimpreso"),
            ("preprinted", "Preimpreso"),
        ],
        string="Modo de Impresión del Remito",
        default="autoprinted",
        required=True,
        help="Argentina: cómo se imprime el remito de este tipo de operación.\n"
        "* Autoimpreso: Odoo imprime el comprobante completo (encabezado, número y CAI), por lo que "
        "el CAI, su vencimiento y el rango autorizado son obligatorios.\n"
        "* Preimpreso: el papel de imprenta ya trae encabezado, numeración y CAI, así que Odoo solo "
        "imprime el contenido variable y numera según las hojas que se consumen. El CAI no se carga "
        "acá porque viene impreso en el papel.",
    )

    l10n_ar_preprinted_report_view_id = fields.Many2one(
        "ir.ui.view",
        string="Plantilla del Remito Preimpreso",
        domain=[("type", "=", "qweb"), ("mode", "=", "primary")],
        ondelete="restrict",
        help="Vista QWeb propia con la que se imprime el remito de este tipo de operación, en lugar "
        "del comprobante estándar. Sirve para adaptar el contenido variable a la grilla del papel "
        "de la imprenta, que cada talonario trae distinta.\n"
        "La plantilla se crea desde Ajustes > Técnico > Vistas y recibe el picking en la variable "
        "'o' (y el tipo de copia en 'copy_type'); tiene que abrir con "
        '<t t-call="web.html_container"> igual que el comprobante estándar.\n'
        "Con una plantilla propia la numeración cuenta TODAS las páginas que se imprimen: cada "
        "página es una hoja del talonario. Vacío, se usa el comprobante estándar.",
    )

    # === CONSTRAINT METHODS === #

    @api.constrains(
        "l10n_ar_voucher_print_mode",
        "l10n_ar_document_type_id",
        "l10n_ar_cai_authorization_code",
        "l10n_ar_cai_expiration_date",
        "l10n_ar_sequence_number_start",
        "l10n_ar_sequence_number_end",
    )
    def _constrains_l10n_ar_voucher_print_mode(self):
        """El CAI y su rango son obligatorios en autoimpreso porque Odoo los imprime. La vista ya los
        pide, pero el modo también puede setearse por import / data / ORM, donde el required de la
        vista no aplica."""
        for picking_type in self.filtered(
            lambda x: x.l10n_ar_document_type_id and x.l10n_ar_voucher_print_mode == "autoprinted"
        ):
            missing = [
                name
                for name, value in (
                    (_("CAI"), picking_type.l10n_ar_cai_authorization_code),
                    (_("CAI Expiration Date"), picking_type.l10n_ar_cai_expiration_date),
                    (_("Sequence From"), picking_type.l10n_ar_sequence_number_start),
                    (_("Sequence To"), picking_type.l10n_ar_sequence_number_end),
                )
                if not value
            ]
            if missing:
                raise ValidationError(
                    _(
                        "En el tipo de operación %(picking_type)s el remito es autoimpreso, así que"
                        " debe completar: %(fields)s.\nSi el papel lo provee una imprenta (ya trae"
                        " encabezado, numeración y CAI), configure el Modo de Impresión del Remito"
                        " como Preimpreso.",
                        picking_type=picking_type.display_name,
                        fields=", ".join(missing),
                    )
                )

    @api.constrains("l10n_ar_preprinted_report_view_id")
    def _constrains_l10n_ar_preprinted_report_view(self):
        """La plantilla tiene que ser una vista QWeb autónoma. El domain del campo ya lo pide,
        pero el modo también puede setearse por import / data / ORM, donde el domain no aplica.

        El chequeo de 'primary' no es cosmético: una vista de herencia (mode = 'extension') no
        tiene arch renderizable propio — es un diff de xpaths — así que el t-call del comprobante
        imprimiría los nodos del diff sueltos en vez del remito."""
        for picking_type in self.filtered("l10n_ar_preprinted_report_view_id"):
            view = picking_type.l10n_ar_preprinted_report_view_id
            if view.type != "qweb" or view.mode != "primary":
                raise ValidationError(
                    _(
                        "La plantilla del remito preimpreso de %(picking_type)s tiene que ser una"
                        " vista QWeb autónoma, y %(view)s es de tipo %(type)s y modo"
                        " %(mode)s.\nCree la plantilla desde Ajustes > Técnico > Vistas con un"
                        " <t t-name> propio, sin vista heredada.",
                        picking_type=picking_type.display_name,
                        view=view.display_name,
                        type=view.type,
                        mode=view.mode,
                    )
                )
