.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=========================================
Remito Preimpreso con plantilla Aeroo
=========================================

Permite imprimir el **remito preimpreso** con una plantilla ``.odt`` propia en
lugar del comprobante qweb de ``l10n_ar_stock_preprinted``.

El papel de un talonario preimpreso lo arma cada imprenta, así que el layout
cambia de cliente a cliente: dónde caen los campos, cuántos renglones entran,
qué espacio queda libre. Un comprobante qweb no se puede acomodar a cada papel
sin tocar el template. Con este módulo el layout es un dato de configuración:
se sube el ``.odt`` en el tipo de operación y listo.

Se instala solo (``auto_install``) cuando la base ya tiene
``l10n_ar_stock_preprinted`` y ``report_aeroo``.

Qué agrega
==========

En el tipo de operación, junto al *Modo de Impresión del Remito* y solo cuando
está en preimpreso:

* **Plantilla del Remito Preimpreso** — el ``.odt`` del talonario.
* **Renglones por Hoja** — cuántos renglones de producto entran en una hoja.

Cómo reemplaza al comprobante
=============================

No agrega una entrada nueva al menú *Imprimir*: el reporte aeroo **reemplaza**
al comprobante de entrega cuando corresponde, así que se sigue imprimiendo desde
donde siempre (el botón de imprimir y el de numerar-e-imprimir).

El reemplazo aplica cuando todos los remitos que se están imprimiendo son de un
mismo tipo de operación preimpreso con plantilla cargada. Un lote mixto —- dos
talonarios distintos, o uno con plantilla y otro sin —- sale por el comprobante
qweb de siempre: no hay un reporte que sirva para los dos.

Es un solo reporte para todos los talonarios: la plantilla no está fija en el
reporte (``tml_source = 'parser'``), se lee del tipo de operación del remito que
se está imprimiendo.

Cómo se cuentan las hojas
=========================

En preimpreso cada hoja consumida se lleva un número de la secuencia, así que
hay que saber cuántas hojas ocupa el remito. Con el comprobante qweb eso se
resuelve renderizando y contando páginas. Con una plantilla ``.odt`` no se
puede: la paginación la decide la plantilla del cliente, no Odoo.

Por eso las hojas se **calculan** a partir de los renglones por hoja del
talonario, que además es el mismo criterio con el que la imprenta armó el papel:

* 25 renglones con 10 renglones por hoja → 3 hojas, 3 números.
* Un remito sin renglones consume igual una hoja.

Los renglones son los mismos que imprime el comprobante de entrega: antes de
validar, los movimientos con cantidad pedida; después, un renglón por movimiento
de detalle cuando se imprimen series y los renglones agregados por producto
cuando no.

Sin plantilla cargada el conteo no cambia: se siguen contando las páginas
renderizadas del comprobante qweb.

Bugs / Roadmap
==============

* Un lote con dos talonarios distintos sale por qweb en vez de partirse en un
  PDF por talonario.
* Los títulos de sección de paquete no cuentan como renglón: se asume que el
  talonario los absorbe.

Credits
=======

Contributors
------------

Images
------

* |company| |icon|

Maintainer
----------

|company_logo|

This module is maintained by the |company|.

To contribute to this module, please visit https://github.com/ingadhoc.
