.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

============================
Remito electrónico Argentino
============================

PENDIENTE:
* validaciones formato patente
* validación requerimiento patente
* parsear datetime_out y validar fecha >= hoy-1 y menor= a hoy mas 30
* asistente de importe y otras mejroas de usabilidad
* Implementar, si es necesario, nro_planta y nro_puerta

IMPORTANTE: por ahora está implementado para stock.picking pero no seria muy dificil implementarlo también para facturas ya que la factura puede ser el comprobante de entrega (ver documentos de más abajo)

Por ahora implementados ARBA y Santa Fe.

* Tabla de códigos (Según arba): http://www.arba.gov.ar/bajadas/Fiscalizacion/Operativos/TransporteBienes/Documentacion/20080701-TB-TablasDeValidacion.pdf
* Tablas de códigos (Según santa fe): https://www.santafe.gov.ar/index.php/content/download/72020/349107/file/Descargar (igual a la de arba)
* Tabla en sistemas ágiles: http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCotArba?format=pdf
* Especificación archivo txt: http://www.arba.gov.ar/Transporte_Bienes/VerPDF.asp?param=DA
* Nomenclador productos: https://www.arba.gov.ar/Aplicaciones/NomencladorTB/NomencladorTB.asp


Installation
============

To install this module, you need to:

#. Do this ...

Configuration
=============

To configure this module, you need to:

#. Go to ...

Usage
=====

To use this module, you need to:

#. Go to ...

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.adhoc.com.ar/

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Known issues / Roadmap
======================

* ...

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ingadhoc/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* ADHOC SA: `Icon <http://fotos.subefotos.com/83fed853c1e15a8023b86b2b22d6145bo.png>`_.

Contributors
------------


Maintainer
----------

.. image:: http://fotos.subefotos.com/83fed853c1e15a8023b86b2b22d6145bo.png
   :alt: Odoo Community Association
   :target: https://www.adhoc.com.ar

This module is maintained by the ADHOC SA.

To contribute to this module, please visit https://www.adhoc.com.ar.
