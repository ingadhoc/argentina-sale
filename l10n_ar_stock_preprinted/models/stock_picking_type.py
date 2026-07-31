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
