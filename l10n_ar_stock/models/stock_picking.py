from odoo import models, fields, _
import re
import datetime
try:
    from pyafipws.iibb import IIBB
except ImportError:
    IIBB = None
from odoo.exceptions import UserError
import os
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):

    _inherit = "stock.picking"

    dispatch_number = fields.Char(
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Si define un número de despacho, al validar la transferencia, '
        'el mismo será asociado a los lotes sin número de despacho vinculados '
        'a la transferencia.'
    )
    document_type_id = fields.Many2one(
        related='book_id.document_type_id',
        readonly=True
    )
    cot_numero_unico = fields.Char(
        'COT - Nro Único',
        help='Número único del último COT solicitado',
    )
    cot_numero_comprobante = fields.Char(
        'COT - Nro Comprobante',
        help='Número de comprobante del último COT solicitado',
    )
    cot = fields.Char(
        'COT',
        help='Número de COT del último COT solicitado',
    )
    l10n_ar_afip_barcode = fields.Char(compute='_compute_l10n_ar_afip_barcode', string='AFIP Barcode',)

    def _compute_l10n_ar_afip_barcode(self):
        for rec in self:
            barcode = False
            if rec.book_id.sequence_id.prefix and rec.book_id.l10n_ar_cai_due \
                    and rec.book_id.l10n_ar_cai and not rec.book_id.lines_per_voucher:
                cae_due = rec.book_id.l10n_ar_cai_due.strftime('%Y%m%d')
                pos_number = int(re.sub('[^0-9]', '', rec.book_id.sequence_id.prefix))
                barcode = ''.join([
                    str(rec.company_id.partner_id.l10n_ar_vat),
                    "%03d" % int(rec.book_id.document_type_id.code),
                    "%05d" % pos_number,
                    rec.book_id.l10n_ar_cai,
                    cae_due])
            rec.l10n_ar_afip_barcode = barcode

    def get_arba_file_data(
            self, datetime_out, tipo_recorrido, carrier_partner,
            patente_vehiculo, patente_acomplado, prod_no_term_dev, importe):
        """
        NOTA: esta implementado como para soportar seleccionar varios remitos
        y mandarlos juntos pero por ahora no le estamos dando uso.
        Tener en cuenta que si se numera con más de un remito nosotros mandamos
        solo el primero ya que para cada remito reportado se debe indicar
        los productos y ese dato no lo tenemos (solo sabemos cuantas hojas
        consume)
        """

        FECHA_SALIDA_TRANSPORTE = datetime_out.strftime('%Y%m%d')
        HORA_SALIDA_TRANSPORTE = datetime_out.strftime('%H%M')

        company = self.mapped('company_id')
        if len(company) > 1:
            raise UserError(_(
                'Los remitos seleccionados deben pertenecer a la misma '
                'compañía'))
        cuit = company.partner_id.ensure_vat()
        cuit_carrier = carrier_partner.ensure_vat()

        if cuit_carrier == cuit and not patente_vehiculo:
            raise UserError(_(
                'Si el CUIT de la compañía y el cuit del transportista son el '
                'mismo, se debe informar la patente del vehículo.'))

        # ej. nombre archivo TB_30111111118_003002_20060716_000183.txt
        # TODO ver de donde obtener estos datos
        nro_planta = '000'
        nro_puerta = '000'
        nro_secuencial = self.env['ir.sequence'].with_context(
            force_company=company.id).next_by_code('arba.cot.file')
        if not nro_secuencial:
            raise UserError(_(
                'No sequence found for COT files (code = "arba.cot.file") on '
                'company "%s') % (company.name))

        filename = "TB_%s_%s%s_%s_%s.txt" % (
            cuit,
            nro_planta,
            nro_puerta,
            datetime.date.today().strftime('%Y%m%d'),
            nro_secuencial)

        # 01 - HEADER: TIPO_REGISTRO & CUIT_EMPRESA
        HEADER = ["01", cuit]

        # 04 - FOOTER (Pie): TIPO_REGISTRO: 04 & CANTIDAD_TOTAL_REMITOS
        # TODO que tome 10 caracteres
        FOOTER = ["04", str(len(self))]

        # TODO, si interesa se puede repetir esto para cada uno
        REMITOS_PRODUCTOS = []

        # recorremos cada voucher number de cada remito
        # for voucher in self.mapped('voucher_ids'):
        #     rec = voucher.picking_id
        for rec in self:
            if not rec.voucher_ids:
                raise UserError(_('No se asignó número de remito'))
            voucher = rec.voucher_ids[0]
            dest_partner = rec.partner_id
            source_partner = rec.picking_type_id.warehouse_id.partner_id or\
                rec.company_id.partner_id
            commercial_partner = dest_partner.commercial_partner_id

            if not source_partner.state_id.code or \
                    not dest_partner.state_id.code:
                raise UserError(_(
                    'Las provincias de origen y destino son obligatorias y '
                    'deben tener un código válido'))

            if not rec.document_type_id:
                raise UserError(_(
                    'Picking has no "Document type" linked (Id: %s)') % (
                    rec.id))
            CODIGO_DGI = rec.document_type_id.code
            CODIGO_DGI = CODIGO_DGI.rjust(3, '0')
            letter = rec.document_type_id.l10n_ar_letter
            if not CODIGO_DGI or not letter:
                raise UserError(_(
                    'Document type has no validator, code or letter configured'
                    ' (Id: %s') % (rec.document_type_id.id))

            # TODO ver de hacer uno por número de remito?
            document_parts = self.env['account.move']._l10n_ar_get_document_number_parts(voucher.name, CODIGO_DGI)
            PREFIJO = str(document_parts['point_of_sale'])
            NUMERO = str(document_parts['invoice_number'])
            PREFIJO = PREFIJO.rjust(5, '0')
            NUMERO = NUMERO.rjust(8, '0')

            # rellenar y truncar a 2
            # TIPO = '{:>2.2}'.format(letter.name)

            # si nro doc y tipo en ‘DNI’, ‘LC’, ‘LE’, ‘PAS’, ‘CI’ y doc
            doc_categ_id = commercial_partner.l10n_latam_identification_type_id
            if commercial_partner.vat and doc_categ_id.name in [
                    'DNI', 'LC', 'LE', 'PAS', 'CI']:
                dest_tipo_doc = doc_categ_id.l10n_ar_afip_code
                dest_doc = commercial_partner.vat
                dest_cuit = ''
            else:
                dest_tipo_doc = ''
                dest_doc = ''
                dest_cuit = commercial_partner.ensure_vat()

            dest_cons_final = commercial_partner.\
                l10n_ar_afip_responsibility_type_id.code == "5" and '1' or '0'

            REMITOS_PRODUCTOS.append([
                "02",  # TIPO_REGISTRO

                # FECHA_EMISION
                # fields.Date.from_string(self.date_done).strftime('%Y%m%d').
                datetime.date.today().strftime('%Y%m%d'),

                # CODIGO_UNICO formato (CODIGO_DGI, TIPO, PREFIJO, NUMERO)
                # ej. 91 |R999900068148|
                "%s%s%s" % (CODIGO_DGI, PREFIJO, NUMERO),

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
                commercial_partner.name[:50],

                # DESTINATARIO_TENEDOR: 0=no, 1=si.
                dest_cons_final and '0' or '1',

                # DESTINO_DOMICILIO_CALLE
                (dest_partner.street or '')[:40],

                # DESTINO_DOMICILIO_NUMERO
                # TODO implementar
                '',

                # DESTINO_DOMICILIO_COMPLE
                # TODO implementar valores ’ ’, ‘S/N’ , ‘1/2’, ‘1/4’, ‘BIS’
                'S/N',

                # DESTINO_DOMICILIO_PISO
                # TODO implementar
                '',

                # DESTINO_DOMICILIO_DTO
                # TODO implementar
                '',

                # DESTINO_DOMICILIO_BARRIO
                # TODO implementar
                '',

                # DESTINO_DOMICILIO_CODIGOP
                (dest_partner.zip or '')[:8],

                # DESTINO_DOMICILIO_LOCALIDAD
                (dest_partner.city or '')[:50],

                # DESTINO_DOMICILIO_PROVINCIA: ver tabla de provincias
                # usa código distinto al de afip
                (dest_partner.state_id.code or '')[:1],

                # PROPIO_DESTINO_DOMICILIO_CODIGO
                # TODO implementar
                '',

                # ENTREGA_DOMICILIO_ORIGEN: 'SI' o 'NO'
                # TODO implementar
                'NO',

                # ORIGEN_CUIT
                cuit,

                # ORIGEN_RAZON_SOCIAL
                company.name[:50],

                # EMISOR_TENEDOR: 0=no, 1=si
                # TODO implementar
                '0',

                # ORIGEN_DOMICILIO_CALLE
                (source_partner.street or '')[:40],

                # ORIGEN DOMICILIO_NUMBERO
                # TODO implementar
                '',

                # ORIGEN_DOMICILIO_COMPLE
                # TODO implementar valores ’ ’, ‘S/N’ , ‘1/2’, ‘1/4’, ‘BIS’
                'S/N',

                # ORIGEN_DOMICILIO_PISO
                # TODO implementar
                '',

                # ORIGEN_DOMICILIO_DTO
                # TODO implementar
                '',

                # ORIGEN_DOMICILIO_BARRIO
                # TODO implementar
                '',

                # ORIGEN_DOMICILIO_CODIGOP
                (source_partner.zip or '')[:8],

                # ORIGEN_DOMICILIO_LOCALIDAD
                (source_partner.city or '')[:50],

                # ORIGEN_DOMICILIO_PROVINCIA: ver tabla de provincias
                (source_partner.state_id.code or '')[:1],

                # TRANSPORTISTA_CUIT
                cuit_carrier,

                # TIPO_RECORRIDO: 'U' urbano, 'R' rural, 'M' mixto
                tipo_recorrido,

                # RECORRIDO_LOCALIDAD: máx. 50 caracteres,
                # TODO implementar
                '',

                # RECORRIDO_CALLE: máx. 40 caracteres
                # TODO implementar
                '',

                # RECORRIDO_RUTA: máx. 40 caracteres
                # TODO implementar
                '',

                # PATENTE_VEHICULO: 3 letras y 3 números
                patente_vehiculo or '',

                # PATENTE_ACOPLADO: 3 letras y 3 números
                patente_acomplado or '',

                # PRODUCTO_NO_TERM_DEV: 0=No, 1=Si (devoluciones)
                prod_no_term_dev,

                # IMPORTE: formato 8 enteros 2 decimales,
                str(int(round(importe * 100.0)))[-14:],
            ])

            for line in rec.mapped('move_lines'):

                # buscamos si hay unidad de medida de la cateogria que tenga
                # codigo de arba y usamos esa, ademas convertimos la cantidad
                product_qty = line.product_uom_qty
                if line.product_uom.arba_code:
                    uom_arba_with_code = line.product_uom
                else:
                    uom_arba_with_code = line.product_uom.search([
                        ('category_id', '=',
                            line.product_uom.category_id.id),
                        ('arba_code', '!=', False)], limit=1)
                    if not uom_arba_with_code:
                        raise UserError(_(
                            'No arba code for uom "%s" (Id: %s) or any uom in '
                            'category "%s"') % (
                            line.product_uom.name, line.product_uom.id,
                            line.product_uom.category_id.name))

                    product_qty = line.product_uom._compute_quantity(
                        product_qty, uom_arba_with_code)

                if not line.product_id.arba_code:
                    raise UserError(_(
                        'No arba code for product "%s" (Id: %s)') % (
                        line.product_id.name, line.product_id.id))

                REMITOS_PRODUCTOS.append([
                    # TIPO_REGISTRO: 03
                    '03',

                    # CODIGO_UNICO_PRODUCTO
                    # nomenclador COT (Transporte de Bienes)
                    line.product_id.arba_code,

                    # RENTAS_CODIGO_UNIDAD_MEDIDA: ver tabla unidades de medida
                    uom_arba_with_code.arba_code,

                    # CANTIDAD: 13 enteros y 2 decimales (no incluir coma
                    # ni punto), ej 200 un -> 20000
                    str(int(round(product_qty * 100.0)))[-15:],

                    # PROPIO_CODIGO_PRODUCTO: máx. 25 caracteres
                    (line.product_id.default_code or '')[:25],

                    # PROPIO_DESCRIPCION_PRODUCTO: máx. 40 caracteres
                    (line.product_id.name)[:40],

                    # PROPIO_DESCRIPCION_UNIDAD_MEDIDA: máx. 20 caracteres
                    (uom_arba_with_code.name)[:20],

                    # CANTIDAD_AJUSTADA: 13 enteros y 2 decimales (no incluir
                    # coma ni punto), ej 200 un -> 20000 (en los que vi mandan
                    # lo mismo)
                    str(int(round(product_qty * 100.0)))[-15:],
                ])

        content = ''
        for line in [HEADER] + REMITOS_PRODUCTOS + [FOOTER]:
            content += '%s\r' % ('|'.join(line))
        return (content, filename)

    def do_pyafipws_presentar_remito(
            self, datetime_out, tipo_recorrido, carrier_partner,
            patente_vehiculo, patente_acomplado, prod_no_term_dev, importe):
        self.ensure_one()

        COT = self.company_id.arba_cot_connect()

        if not carrier_partner:
            raise UserError(
                'Debe vincular una "Empresa transportista" a la forma de envío'
                ' seleccionada o elegir otra forma de envío')
        content, filename = self.get_arba_file_data(
            datetime_out, tipo_recorrido, carrier_partner,
            patente_vehiculo, patente_acomplado,
            prod_no_term_dev, importe)

        # NO podemos usar tmp porque agrega un sufijo distinto y arba exije
        # que sea tal cual el nombre del archivo
        # with tempfile.NamedTemporaryFile(
        #         prefix=filename, suffix='.txt') as file:
        #     file.write(content.encode('utf-8'))
        #     COT.PresentarRemito(file.name, testing="")

        filename = '/tmp/%s' % filename
        file = open(filename, 'w')
        file.write(content)
        file.close()
        _logger.info('Presentando COT con archivo "%s"' % filename)
        COT.PresentarRemito(filename, testing="")
        os.remove(filename)

        if COT.TipoError:
            msg = _(
                'Error al presentar remito:\n'
                '* Tipo Error: %s\n'
                '* Codigo Error: %s\n'
                '* Mensaje Error: %s') % (
                    COT.TipoError, COT.CodigoError, COT.MensajeError)
            _logger.warning(msg)
            raise UserError(msg)
        elif COT.Excepcion:
            msg = _('Error al presentar remito:\n* %s') % COT.Excepcion
            _logger.warning(msg)
            raise UserError(msg)

        errors = []
        while COT.LeerErrorValidacion():
            errors.append((
                "* MensajeError: %s\n"
                "* TipoError: %s\n"
                "* CodigoError: %s\n") % (
                    COT.MensajeError, COT.TipoError, COT.CodigoError))

        if errors:
            raise UserError(_(
                "Error al presentar remito:\n%s") % '\n'.join(errors))

        # TODO deberiamos tratar de usar este archivo y no generar el de arriba
        attachments = [(filename, content)]
        body = """
<p>
    Resultado solictud COT:
    <ul>
        <li>Número Comprobante: %s</li>
        <li>Codigo Integridad: %s</li>
        <li>Procesado: %s</li>
        <li>Número Único: %s</li>
        <li>COT: %s</li>
    </ul>
</p>
""" % (COT.NumeroComprobante, COT.CodigoIntegridad,
            COT.Procesado, COT.NumeroUnico, COT.COT)

        self.write({
            'cot_numero_unico': COT.NumeroComprobante,
            'cot_numero_comprobante': COT.NumeroUnico,
            'cot': COT.COT,
        })
        self.message_post(
            body=body,
            subject=_('Remito Electrónico Solicitado'),
            attachments=attachments)

        return True

    def action_done(self):
        res = super().action_done()
        for rec in self.filtered(
                lambda x: x.picking_type_code == 'incoming' and
                x.dispatch_number):
            rec.move_line_ids.filtered(
                lambda l: l.lot_id and not l.lot_id.dispatch_number).mapped(
                    'lot_id').write({'dispatch_number': rec.dispatch_number})
        return res
