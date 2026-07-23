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

Un casillero **Autoimpreso** en el tipo de operación define el modo:

* **Autoimpreso** (tildado) — Odoo imprime el comprobante completo (encabezado,
  número y CAI); el CAI es obligatorio. Se numera con un único número por
  transferencia (comportamiento estándar de ``l10n_ar_stock``).
* **Preimpreso** (destildado) — el papel de imprenta ya trae encabezado,
  numeración y CAI. No se pide CAI y Odoo solo imprime el contenido variable,
  numerando según las hojas consumidas.

Qué agrega
==========

* ``stock.picking.type.l10n_ar_autoprinted``: casillero *Autoimpreso* (por
  defecto verdadero). Al destildarlo, el CAI deja de pedirse y aparecen los
  *Renglones por Remito*.
* ``stock.picking.type.l10n_ar_is_preprinted`` (computado): verdadero cuando hay
  documento de remito y el tipo **no** es autoimpreso. Lo usan el reporte y la
  numeración.
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
#. Destildar *Autoimpreso* (así el tipo pasa a preimpreso).
#. Opcionalmente cargar *Renglones por Remito*.

Credits
=======

|company| |company_logo|
