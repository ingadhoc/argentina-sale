from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_name_delivery_report(self, report_xml_id):
        """Si el tipo de operación tiene plantilla propia, el remito se imprime con esa.

        Devolvemos el key y no el external id porque el t-call resuelve los templates por
        ir.ui.view.key (_get_template_domain), y una vista hecha desde la interfaz no tiene
        external id; key en cambio siempre tiene: lo exige el constraint _qweb_required_key de
        base, y Odoo lo autogenera cuando no se lo dan. Una plantilla que llega como data de un
        módulo también tiene key, así que las dos formas de crearla entran por acá.

        No filtramos por país: el campo es de la localización argentina y solo se carga en ese
        flujo, y si alguien lo cargó, imprimir con esa plantilla es lo que pidió."""
        self.ensure_one()
        custom_view = self.picking_type_id.l10n_ar_delivery_report_view_id
        if custom_view:
            return custom_view.key
        return super()._get_name_delivery_report(report_xml_id)
