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
variable (productos, cliente) y numera la entrega según las hojas que realmente
se imprimen.

Cómo se distingue del autoimpreso
=================================

El modo se **autocalcula según el CAI** del tipo de operación:

* **Autoimpreso** — el tipo de operación tiene CAI cargado. Odoo imprime el
  comprobante completo (encabezado, número y CAI) y numera con un único número
  por transferencia (comportamiento estándar de ``l10n_ar_stock``).
* **Preimpreso** — el tipo de operación tiene un tipo de documento de remito
  pero **no** tiene CAI. Este módulo habilita ese caso relajando la
  obligatoriedad del CAI.

Qué agrega
==========

* ``stock.picking.type.l10n_ar_autoprinted`` (computado): casillero *Autoimpreso*
  de solo lectura; verdadero cuando hay CAI cargado.
* ``stock.picking.type.l10n_ar_is_preprinted`` (computado): verdadero cuando hay
  documento de remito y no hay CAI. Lo usan el reporte y la numeración.
* Numeración: al generar la guía de remito en un tipo preimpreso, se renderiza el
  comprobante de entrega, se cuentan las **hojas (páginas) que se imprimen** y se
  asignan tantos números consecutivos como hojas, separados por coma y sin datos
  de CAI.
* Reporte: en preimpreso el remito se imprime sin encabezado, sin número y sin
  CAI (ya vienen en el papel).

Configuración
=============

En *Inventario > Configuración > Tipos de operación*, para un tipo de operación
de salida:

#. Definir el *Tipo de documento* de remito.
#. Dejar el *CAI* vacío (así el casillero *Autoimpreso* queda destildado y el
   tipo pasa a preimpreso).

Credits
=======

|company| |company_logo|
