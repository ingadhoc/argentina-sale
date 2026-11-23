from odoo import models

DELIVERY_REPORT = "stock.action_report_delivery"
PREPRINTED_AEROO_REPORT = "l10n_ar_stock_preprinted_aeroo.report_delivery_preprinted_aeroo"


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def report_action(self, docids, data=None, config=True):
        """El botón Imprimir del remito y el de numerar-e-imprimir apuntan siempre al comprobante
        de entrega qweb. Cuando todos los remitos del lote tienen plantilla .odt, imprimimos el
        reporte aeroo en su lugar: es el mismo comprobante, con el layout del talonario del
        cliente. Reemplazamos acá y no en cada botón para tomar los dos caminos con un solo
        override."""
        aeroo_report = self._l10n_ar_preprinted_aeroo_report(docids)
        if aeroo_report:
            return aeroo_report.report_action(docids, data=data, config=config)
        return super().report_action(docids, data=data, config=config)

    def _l10n_ar_preprinted_aeroo_report(self, docids):
        """El reporte aeroo con el que hay que reemplazar este, o False si no aplica.

        Pedimos un solo tipo de operación a propósito: con un lote mixto (un remito con plantilla
        y otro sin, o dos talonarios distintos) no hay un reporte que sirva para todos, así que se
        imprime el comprobante qweb, que es el comportamiento de siempre. No hay recursión porque
        el reporte que devolvemos nunca es el comprobante de entrega."""
        delivery_report = self.env.ref(DELIVERY_REPORT, raise_if_not_found=False)
        if len(self) != 1 or not delivery_report or self != delivery_report:
            return False
        pickings = docids if isinstance(docids, models.Model) else self.env["stock.picking"].browse(docids)
        if not pickings or pickings._name != "stock.picking":
            return False
        if len(pickings.picking_type_id) != 1:
            return False
        if not all(picking._l10n_ar_preprinted_aeroo_template() for picking in pickings):
            return False
        return self.env.ref(PREPRINTED_AEROO_REPORT, raise_if_not_found=False)
