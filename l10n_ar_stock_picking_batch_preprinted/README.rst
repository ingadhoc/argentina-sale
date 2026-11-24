.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=========================================
Remito de Lote Preimpreso para Argentina
=========================================

Hace que el remito de un lote con cliente se comporte, en un tipo de operación
**preimpreso**, igual que el de una entrega. Se instala solo cuando están
instalados ``l10n_ar_stock_picking_batch`` y ``l10n_ar_stock_preprinted``.

Qué cambia
==========

* Numeración: al generar el remito del lote se cuentan las **hojas del reporte del
  lote** (que lleva los productos de todas sus entregas) y se asignan tantos números
  consecutivos como hojas. Esa lista es el remito del lote y se copia en todas sus
  entregas. Si el tipo de operación tiene duplicado o triplicado, el conteo corre
  sobre una sola copia.
* Formato: con el remito generado, el reporte del lote se imprime sin encabezado,
  sin número y sin CAI, y con el pie vacío, como el de la entrega.

En un tipo de operación autoimpreso no cambia nada.

Credits
=======

|company| |company_logo|
