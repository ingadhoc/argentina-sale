# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
# import openerp.tools as tools
try:
    from pyafipws.iibb import IIBB
except ImportError:
    IIBB = None
from openerp.exceptions import UserError
import tempfile
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):

    _inherit = "stock.picking"

    document_type_id = fields.Many2one(
        related='book_id.document_type_id',
        readonly=True
    )

    # def get_arba_data(self, partner, date):
    @api.multi
    def get_arba_file_data(
            self, datetime_out, tipo_recorrido, carrier_partner,
            patente_vehiculo=False, patente_acomplado=False,
            prod_no_term_dev='0', importe=0.0):
        # TODO parsear datetime_out y validar fecha >= hoy-1 y menor= a hoy mas 30
        HORA_SALIDA_TRANSPORTE = datetime_out
        FECHA_SALIDA_TRANSPORTE = datetime_out

        companies = self.mapped('company_id')
        if len(companies) > 1:
            raise UserError(_(
                'Los remitos seleccionados deben pertenecer a la misma '
                'compañía'))
        cuit = companies.cuit_required()

        # ej. nombre archivo TB_30111111118_003002_20060716_000183.txt
        # TODO ver de donde obtener estos datos
        nro_planta = '000'
        nro_puerta = '002'
        nro_secuencial = '000183'

        filename = "TB_%s_%s_%s_%s_%s.txt" % (
            cuit,
            nro_planta,
            nro_puerta,
            fields.Date.today(),
            # self.date,
            nro_secuencial)

        # 01 - HEADER: TIPO_REGISTRO & CUIT_EMPRESA
        HEADER = ["01", cuit]

        # 04 - FOOTER (Pie): TIPO_REGISTRO: 04 & CANTIDAD_TOTAL_REMITOS
        # TODO que tome 10 caracteres
        FOOTER = ["04", '1']
        '\n'.join([])

        # TODO, si interesa se puede repetir esto para cada uno
        REMITOS = []
        # recorremos cada voucher number de cada remito
        for voucher in self.mapped('voucher_ids'):
            rec = voucher.picking_id
            dest_partner = rec.partner_id
            source_partner = rec.picking_type_id.warehouse_id.partner_id or\
                rec.company_id.partner_id
            commercial_partner = dest_partner.commercial_partner_id

            if not rec.document_type_id:
                raise UserError(_(
                    'Picking has no "Document type" linked (Id: %s') % (
                    rec.id))
            validator = rec.document_type_id.validator_id
            CODIGO_DGI = rec.document_type_id.code
            letter = rec.document_type_id.document_letter_id
            if not validator or not CODIGO_DGI or not letter:
                raise UserError(_(
                    'Document type has no validator, code or letter configured'
                    ' (Id: %s') % (rec.document_type_id.id))

            # TODO ver de hacer uno por número de remito?
            PREFIJO, NUMERO = validator.validate_value(
                voucher.name, return_parts=True)
            TIPO = letter.name.rjust(2, ' ')

            # si nro doc y tipo en ‘DNI’, ‘LC’, ‘LE’, ‘PAS’, ‘CI’ y doc
            doc_categ_id = commercial_partner.main_id_category_id
            if commercial_partner.main_id_number and doc_categ_id.code in [
                    'DNI', 'LC', 'LE', 'PAS', 'CI']:
                dest_tipo_doc = doc_categ_id.code
                dest_doc = commercial_partner.main_id_number
            else:
                dest_tipo_doc = ''
                dest_doc = ''

            dest_tipo_doc = dest_tipo_doc.rjust(3, " ")
            dest_doc = dest_doc.rjust(11, " ")

            dest_cons_final = commercial_partner.afip_responsability_type_id \
                == "5" and '1' or '0'

            dest_cuit = commercial_partner.cuit.rjust(11, ' ')

            REMITOS.append([
                "02",  # TIPO_REGISTRO
                self.date_done,  # FECHA_EMISION

                # CODIGO_UNICO formato (CODIGO_DGI, TIPO, PREFIJO, NUMERO)
                # ej. 91 |R999900068148|
                "%s%s%s%s" % (CODIGO_DGI, TIPO, PREFIJO, NUMERO),

                # FECHA_SALIDA_TRANSPORTE: formato AAAAMMDD
                FECHA_SALIDA_TRANSPORTE,

                # HORA_SALIDA_TRANSPORTE: formato HHMM
                HORA_SALIDA_TRANSPORTE,

                # SUJETO_GENERADOR: 'E' emisor, 'D' destinatario
                'E',

                # DESTINATARIO_CONSUMIDOR_FINAL: 0 no, 1 sí
                dest_cons_final,

                # DESTINATARIO_TIPO_DOCUMENTO: 'DNI', 'LE', 'PAS', 'CI'
                dest_tipo_doc,

                # DESTINATARIO_DOCUMENTO
                dest_doc,

                # DESTIANTARIO_CUIT
                dest_cuit,

                # DESTINATARIO_RAZON_SOCIAL
                commercial_partner.name,

                # DESTINATARIO_TENEDOR: 0=no, 1=si.
                dest_cons_final and '0' or '1',

                # DESTINO_DOMICILIO_CALLE
                # esto rellena y trunca
                '{:40.40}'.format(dest_partner.street),

                # DESTINO_DOMICILIO_NUMERO
                # TODO implementar
                '{:5}'.format(' '),

                # DESTINO_DOMICILIO_COMPLE
                # TODO implementar valores ’ ’, ‘S/N’ , ‘1/2’, ‘1/4’, ‘BIS’
                'S/N',

                # DESTINO_DOMICILIO_PISO
                # TODO implementar
                '{:5}'.format(' '),

                # DESTINO_DOMICILIO_DTO
                # TODO implementar
                '{:3}'.format(' '),

                # DESTINO_DOMICILIO_BARRIO
                # TODO implementar
                '{:30}'.format(' '),

                # DESTINO_DOMICILIO_CODIGOP
                '{:8}'.format(dest_partner.zip or ''),

                # DESTINO_DOMICILIO_LOCALIDAD
                '{:50}'.format(dest_partner.city or ''),

                # DESTINO_DOMICILIO_PROVINCIA: ver tabla de provincias
                # usa código distinto al de afip
                '{:50}'.format(dest_partner.state_id.code),

                # PROPIO_DESTINO_DOMICILIO_CODIGO
                # TODO implementar
                '{:20}'.format(' '),

                # ENTREGA_DOMICILIO_ORIGEN: 'SI' o 'NO'
                # TODO implementar
                'NO',

                # ORIGEN_CUIT
                cuit,

                # ORIGEN_RAZON_SOCIAL
                companies.name,

                # EMISOR_TENEDOR: 0=no, 1=si
                # TODO implementar
                '0',

                # ORIGEN_DOMICILIO_CALLE
                # esto rellena y trunca
                '{:40.40}'.format(source_partner.street),

                # ORIGEN DOMICILIO_NUMBERO
                # TODO implementar
                '{:5}'.format(' '),

                # ORIGEN_DOMICILIO_COMPLE
                # TODO implementar valores ’ ’, ‘S/N’ , ‘1/2’, ‘1/4’, ‘BIS’
                'S/N',

                # ORIGEN_DOMICILIO_PISO
                # TODO implementar
                '{:5}'.format(' '),

                # ORIGEN_DOMICILIO_DTO
                # TODO implementar
                '{:3}'.format(' '),

                # ORIGEN_DOMICILIO_BARRIO
                # TODO implementar
                '{:30}'.format(' '),

                # ORIGEN_DOMICILIO_CODIGOP
                '{:8}'.format(source_partner.zip or ''),

                # ORIGEN_DOMICILIO_LOCALIDAD
                '{:50}'.format(source_partner.city or ''),

                # ORIGEN_DOMICILIO_PROVINCIA: ver tabla de provincias
                '{:50}'.format(source_partner.state_id.code),

                # TRANSPORTISTA_CUIT
                carrier_partner.cuit_required(),

                # TIPO_RECORRIDO: 'U' urbano, 'R' rural, 'M' mixto
                tipo_recorrido,

                # RECORRIDO_LOCALIDAD: máx. 50 caracteres,
                # TODO implementar
                '{:50}'.format(' '),

                # RECORRIDO_CALLE: máx. 40 caracteres
                # TODO implementar
                '{:40}'.format(' '),

                # RECORRIDO_RUTA: máx. 40 caracteres
                # TODO implementar
                '{:40}'.format(' '),

                # PATENTE_VEHICULO: 3 letras y 3 números
                patente_vehiculo or '',

                # PATENTE_ACOPLADO: 3 letras y 3 números
                patente_acomplado or '',

                # PRODUCTO_NO_TERM_DEV: 0=No, 1=Si (devoluciones)
                prod_no_term_dev,

                # IMPORTE: formato 8 enteros 2 decimales,
                str(round(importe * 100.0))[-10:],
            ])

        PRODUCTOS = []
        for line in self.mapped('pack_operation_ids'):
            if not line.product_uom_id.arba_code:
                raise UserError(_('No arba code for uom %s (Id: %s') % (
                    line.product_uom_id.name, line.product_uom_id.id))
            if not line.product_id.arba_code:
                raise UserError(_('No arba code for product %s (Id: %s') % (
                    line.product_id.name, line.product_id.id))

            PRODUCTOS.append([
                # TIPO_REGISTRO: 03
                '03',

                # CODIGO_UNICO_PRODUCTO nomenclador COT (Transporte de Bienes)
                line.product_id.arba_code,

                # RENTAS_CODIGO_UNIDAD_MEDIDA: ver tabla unidades de medida
                line.product_uom_id.arba_code,

                # CANTIDAD: 13 enteros y 2 decimales (no incluir coma ni punto)
                # , ej 200 un -> 20000
                str(round(line.product_qty * 100.0))[-15:],

                # PROPIO_CODIGO_PRODUCTO: máx. 25 caracteres
                '{:.25}'.format(line.product_id.default_code),

                # PROPIO_DESCRIPCION_PRODUCTO: máx. 40 caracteres
                '{:.40}'.format(line.product_id.name),

                # PROPIO_DESCRIPCION_UNIDAD_MEDIDA: máx. 20 caracteres
                '{:.20}'.format(line.product_uom_id.name),

                # CANTIDAD_AJUSTADA: 13 enteros y 2 decimales (no incluir coma
                # ni punto), ej 200 un -> 20000 (en los que vi mandan lo mismo)
                str(round(line.product_qty * 100.0))[-15:],
            ])

        content = ''
        print '[HEADER] + REMITOS + PRODUCTOS + [FOOTER]', [HEADER] + REMITOS + PRODUCTOS + [FOOTER]
        for line in [HEADER] + REMITOS + PRODUCTOS + [FOOTER]:
            print 'line', line
            print 'line 2', '|'.join(line)
            content += '%s\n' % ('|'.join(line))

        return (content, filename)

    @api.multi
    def do_pyafipws_presentar_remito(self):
        self.ensure_one()

        COT = self.company_id.arba_cot_connect()

        with tempfile.NamedTemporaryFile() as file:
            print 'file.name', file.name
            COT.PresentarRemito(file.name, testing="")
        print 'COT.Excepcion', COT.Excepcion
        if COT.Excepcion:
            raise UserError(_(
                "Errores:\n"
                "* MensajeError: %s\n"
                "* TipoError: %s\n"
                "* CodigoError: %s\n") % (
                    COT.MensajeError, COT.TipoError, COT.CodigoError))
        print 'COT.NumeroComprobante', COT.NumeroComprobante
        print 'COT.CodigoIntegridad', COT.CodigoIntegridad
        print 'COT.Procesado', COT.Procesado
        print 'COT.NumeroUnico', COT.NumeroUnico

        return True

    @api.multi
    def do_pyafipws_lee_validacion_remito(self):
        COT = self.company_id.arba_cot_connect()
        while COT.LeerValidacionRemito():
            print "Numero Unico: %s" % COT.NumeroUnico
            print "Procesado: %s" % COT.Procesado
            while COT.LeerErrorValidacion():
                print "Error Validacion: %s | %s" % (
                    COT.CodigoError, COT.MensajeError)
        print "p1 %s" % COT.ObtenerTagXml(
            'validacionesRemitos', 'remito', 1, 'procesado')
