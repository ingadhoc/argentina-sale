.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===============================
Remito Preimpreso para Argentina
===============================

Reincorpora el soporte de **remitos preimpresos de imprenta** sobre el flujo de
remitos argentinos de ``l10n_ar_stock`` / ``l10n_ar_stock_ux``.

Un remito preimpreso es papel provisto por una imprenta que ya trae impresos el
encabezado, la numeración y el CAI. En ese caso Odoo solo imprime el contenido
variable (productos, cliente) y numera las transferencias según los comprobantes
(hojas) que consume.

Cómo se distingue del autoimpreso
=================================

El modo se **deriva del tipo de operación**, sin campos nuevos que el usuario
deba marcar:

* **Autoimpreso** — el tipo de operación tiene CAI cargado. Se imprime el
  comprobante completo (encabezado, número y CAI) y se numera con un único
  número por transferencia (comportamiento estándar de ``l10n_ar_stock``).
* **Preimpreso** — el tipo de operación tiene un tipo de documento de remito
  configurado pero **no** tiene CAI (el CAI viene impreso en el papel). Este
  módulo habilita ese caso relajando la obligatoriedad del CAI.

Qué agrega
==========

* ``stock.picking.type.l10n_ar_is_preprinted`` (computado): indica si el tipo de
  operación es preimpreso (tiene documento de remito y no tiene CAI).
* ``stock.picking.type.l10n_ar_lines_per_voucher``: renglones que entran en cada
  hoja preimpresa. Se usa para calcular cuántos números consume una entrega
  larga. Si es 0, cada entrega consume un único número.
* Numeración: al generar la guía de remito en un tipo preimpreso, se asignan
  tantos números consecutivos como hojas consuma la entrega
  (``ceil(renglones / renglones_por_hoja)``), separados por coma, sin datos de
  CAI.
* Reporte: en preimpreso el remito se imprime sin encabezado, sin número y sin
  CAI (ya vienen en el papel).

Configuración
=============

En *Inventario > Configuración > Tipos de operación*, para un tipo de operación
de salida:

#. Definir el *Tipo de documento* de remito.
#. Dejar el *CAI* vacío (así el tipo pasa a preimpreso).
#. Opcionalmente cargar *Renglones por Remito*.

Credits
=======

|company| |company_logo|
