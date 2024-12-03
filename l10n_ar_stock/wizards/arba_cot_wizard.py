##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api
from odoo.exceptions import ValidationError

import re


class ArbaCotWizard(models.TransientModel):
    _name = 'arba.cot.wizard'
    _description = 'arba.cot.wizard'

    datetime_out = fields.Datetime(
        required=True,
        help='Fecha de salida. No debe ser inferior a ayer ni superior a '
        'dentro de 30 días.'
    )
    tipo_recorrido = fields.Selection(
        [('U', 'Urbano'), ('R', 'Rural'), ('M', 'Mixto')],
        required=True,
        default='M',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Transportista",
        required=True,
    )

    patente_vehiculo = fields.Char(
        help='Requerido si CUIT Transportista = CUIT Compañía\n'
        '3 letras y 3 numeros o 2 letras, 3 números y 2 letras'
    )
    patente_acoplado = fields.Char(
        help='3 letras y 3 numeros o 2 letras, 3 números y 2 letras'
    )
    prod_no_term_dev = fields.Selection(
        [('0', 'No'), ('1', 'Si')],
        string='Productos no terminados / devoluciones',
        default='0',
        required=True,
    )
    # TODO implementar asistente de importe
    importe = fields.Float(
        string='Importe Neto',
    )

    @api.constrains('patente_vehiculo', 'patente_acoplado')
    def _constrain_check_format_patente(self):
        formato_antiguo = r'^[A-Z]{2}\d{3}[A-Z]{2}$'  # LLNNNLL
        formato_nuevo = r'^[A-Z]{3}\d{3}$'            # LLLNNN
        patente_vehiculo_valida = patente_acoplado_valida = False

        if not self.patente_vehiculo and not self.patente_acoplado:
            return True
    
        if self.patente_vehiculo and (re.match(formato_antiguo, self.patente_vehiculo.upper())
           or re.match(formato_nuevo, self.patente_vehiculo)):
            patente_vehiculo_valida = True

        if self.patente_acoplado:
            if bool(re.match(formato_antiguo, self.patente_acoplado.upper())) \
             or bool(re.match(formato_nuevo, self.patente_acoplado)):
                patente_acoplado_valida = True

        error = []
        if not patente_acoplado_valida:
            error.append("Patente Acoplado")
        if not patente_vehiculo_valida:
            error.append("Patente Vehiculo")
        if error:
            raise ValidationError(self.env._("El formato de patente no es válido (%s)" % ', '.join(error)))

    def confirm(self):
        self.ensure_one()
        if self._context.get('active_model') != 'stock.picking':
            return True
        pickings = self.env['stock.picking'].browse(
            self._context.get('active_ids'))
        pickings.do_pyafipws_presentar_remito(
            fields.Date.from_string(self.datetime_out), self.tipo_recorrido,
            self.partner_id, self.patente_vehiculo,
            self.patente_acoplado, self.prod_no_term_dev, self.importe)
