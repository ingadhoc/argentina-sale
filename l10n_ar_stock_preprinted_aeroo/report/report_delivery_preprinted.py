from base64 import b64decode

from odoo import models


class ReportDeliveryPreprinted(models.AbstractModel):
    _name = "report.l10n_ar_preprinted_aeroo"
    _inherit = "report.report_aeroo.abstract"
    _description = "Remito Preimpreso Aeroo"

    def aeroo_report(self, docids, data):
        """Aeroo resuelve la plantilla de un reporte ``tml_source = 'parser'`` con el ``active_id``
        del contexto y, si no está, con ``data['id']`` (``report_parser.py``, ``complex_report``).
        Imprimiendo desde un botón no viene ninguno de los dos —- ``data`` llega en ``None`` y la
        expresión ni siquiera se puede evaluar -—, así que fijamos el registro acá, que es el único
        punto del flujo donde tenemos los docids con seguridad.

        Tomamos el primero: el reemplazo del comprobante exige un solo tipo de operación por lote,
        así que todos los remitos del lote comparten talonario."""
        parser = self.with_context(active_id=docids[0])
        return super(ReportDeliveryPreprinted, parser).aeroo_report(docids, data or {})

    def get_template(self, record):
        """Hook de aeroo para ``tml_source = 'parser'``: la plantilla no es fija, sale del tipo de
        operación del remito que se está imprimiendo. Así un solo reporte sirve para todos los
        talonarios del cliente y la plantilla queda como dato de configuración, en vez de un
        reporte hecho a mano por cada tipo de operación."""
        template = record._l10n_ar_preprinted_aeroo_template()
        return b64decode(template) if template else False
