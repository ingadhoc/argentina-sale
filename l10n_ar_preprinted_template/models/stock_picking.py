from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_name_delivery_report(self, report_xml_id):
        """Si el tipo de operación tiene plantilla propia, el remito preimpreso se imprime con esa.

        Devolvemos el key y no el external id porque el t-call resuelve los templates por
        ir.ui.view.key (_get_template_domain), y una vista hecha desde la interfaz no tiene
        external id; key en cambio siempre tiene: lo exige el constraint _qweb_required_key de
        base, y Odoo lo autogenera cuando no se lo dan. Una plantilla que llega como data de un
        módulo también tiene key, así que las dos formas de crearla entran por acá.

        La plantilla se aplica SOLO en preimpreso, y es una decisión deliberada, no un límite
        del mecanismo: el hook y el constraint sirven igual en autoimpreso (una vista primary
        que hereda el comprobante estándar conserva encabezado, número y CAI, así que el caso
        "agregar campos" funcionaría tal cual). No lo abrimos porque hoy no hay demanda de
        perso en autoimpreso: el día que aparezca, se saca esta condición y se define ahí el
        aviso al guardar que hoy no hace falta — una plantilla dibujada desde cero en
        autoimpreso sale sin número y sin CAI, y el papel está en blanco. Mientras siga
        cerrado, el cliente que pasa de preimpreso a remito digital deja de usar la plantilla
        sin tener que borrarla: se ignora sola.
        """
        self.ensure_one()
        custom_view = self.picking_type_id.l10n_ar_delivery_report_view_id
        if custom_view and self.l10n_ar_voucher_print_mode == "preprinted":
            return custom_view.key
        return super()._get_name_delivery_report(report_xml_id)
