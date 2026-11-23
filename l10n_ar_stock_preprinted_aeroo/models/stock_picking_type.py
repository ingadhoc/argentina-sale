from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_ar_preprinted_template = fields.Binary(
        string="Plantilla del Remito Preimpreso",
        attachment=True,
        help="Plantilla .odt con el layout del talonario de la imprenta. Si se carga, el remito de "
        "este tipo de operación se imprime con esta plantilla en lugar del comprobante estándar de "
        "Odoo. La plantilla es un dato de configuración: no hace falta crear un reporte a mano.",
    )
    l10n_ar_preprinted_template_filename = fields.Char()
    l10n_ar_preprinted_lines_per_sheet = fields.Integer(
        string="Renglones por Hoja",
        help="Cuántos renglones de producto entran en una hoja del talonario. Con plantilla .odt "
        "las hojas no se cuentan renderizando (la paginación la decide la plantilla, no Odoo), se "
        "calculan con este número: un remito de 25 renglones con 10 renglones por hoja consume 3 "
        "hojas, o sea 3 números de la secuencia.",
    )

    # === CONSTRAINT METHODS === #

    @api.constrains("l10n_ar_preprinted_template", "l10n_ar_preprinted_lines_per_sheet")
    def _constrains_l10n_ar_preprinted_lines_per_sheet(self):
        """Sin renglones por hoja el conteo devolvería siempre una hoja y el remito consumiría un
        solo número aunque ocupe varias, que es justo lo que el preimpreso tiene que evitar. Solo
        se exige cuando hay plantilla cargada: sin plantilla imprime el comprobante qweb y las
        hojas se siguen contando renderizando."""
        for picking_type in self.filtered(lambda x: x.l10n_ar_preprinted_template):
            if picking_type.l10n_ar_preprinted_lines_per_sheet <= 0:
                raise ValidationError(
                    _(
                        "En el tipo de operación %(picking_type)s cargó una plantilla de remito"
                        " preimpreso, así que debe indicar cuántos renglones entran en una hoja del"
                        " talonario. Es el número con el que se calcula cuántas hojas (y cuántos"
                        " números) consume cada remito.",
                        picking_type=picking_type.display_name,
                    )
                )
