.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==================================
Remito Preimpreso para Argentina
==================================

Reincorpora el soporte de **remitos preimpresos de imprenta** sobre el flujo de
remitos argentinos de ``l10n_ar_stock`` / ``l10n_ar_stock_ux``.

Un remito preimpreso es papel provisto por una imprenta que ya trae impresos el
encabezado, la numeración y el CAI. En ese caso Odoo solo imprime el contenido
variable (productos, cliente) y numera la entrega según las hojas que realmente
se imprimen.

Cómo se distingue del autoimpreso
=================================

El modo es una **decisión explícita** del tipo de operación, en el campo
*Modo de Impresión del Remito*:

* **Autoimpreso** (default) — Odoo imprime el comprobante completo (encabezado,
  número y CAI) y numera con un único número por transferencia (comportamiento
  estándar de ``l10n_ar_stock``). El CAI, su vencimiento y el rango autorizado
  son obligatorios porque Odoo los imprime.
* **Preimpreso** — el papel de imprenta ya trae encabezado, numeración y CAI.
  Odoo solo imprime el contenido variable y numera según las hojas que se
  consumen. El CAI, su vencimiento y el rango se ocultan y dejan de pedirse.

Qué agrega
==========

* ``stock.picking.type.l10n_ar_voucher_print_mode`` (selección, almacenada):
  *Autoimpreso* / *Preimpreso*. Lo usan la vista, el reporte y la numeración.
  Una restricción de servidor exige CAI, vencimiento y rango cuando el modo es
  autoimpreso (la vista sola no cubre imports ni escrituras por ORM).
* Numeración: al generar la guía de remito en un tipo preimpreso, se renderiza el
  comprobante de entrega, se cuentan las **hojas (páginas) que se imprimen** y se
  asignan tantos números consecutivos como hojas, separados por coma y sin datos
  de CAI. Si el reporte está configurado con duplicado/triplicado, el juego de
  copias consume un solo número por hoja.
* Reporte: en preimpreso el remito se imprime sin encabezado, sin número y sin
  CAI (ya vienen en el papel).
* ``stock.picking.type.l10n_ar_preprinted_report_view_id`` (opcional): plantilla
  QWeb propia con la que se imprime el remito de ese tipo de operación, en lugar
  del comprobante estándar. Ver *Plantilla propia* más abajo.

Plantilla propia
================

Cada imprenta entrega el talonario con su propia grilla, y el comprobante
estándar no siempre cae donde el papel lo espera. Para eso el tipo de operación
acepta una **plantilla QWeb propia**, que la hace un consultor funcional desde la
interfaz —sin módulo, sin deploy— en *Ajustes > Técnico > Vistas*:

#. Crear una vista de tipo *QWeb* con un ``<t t-name="...">`` propio. No es una
   herencia del comprobante estándar: es una plantilla desde cero, dibujada para
   la grilla del papel.
#. La plantilla recibe el picking en la variable ``o`` y el tipo de copia en
   ``copy_type``, y tiene que abrir con ``<t t-call="web.html_container">`` igual
   que el comprobante estándar.
#. Seleccionarla en *Plantilla del Remito Preimpreso*, en el tipo de operación.

Vacío el campo, se usa el comprobante estándar y no cambia nada.

**Numeración con plantilla propia.** El comprobante estándar descuenta del conteo
las hojas que solo traen firma, totales o datos del transportista, apoyándose en
una marca invisible que imprime por cada línea de producto. Una plantilla propia
no emite esa marca, así que el criterio cambia: se cuentan **todas las páginas**
que se imprimen, porque una plantilla dibujada para el papel de la imprenta no
emite hojas que no sean del talonario. El juego de copias
(duplicado / triplicado) sigue consumiendo un solo número por hoja.

Configuración
=============

En *Inventario > Configuración > Tipos de operación*, para un tipo de operación
de salida:

#. Definir el *Tipo de documento* de remito.
#. Poner *Modo de Impresión del Remito* en **Preimpreso**.
#. Ajustar el *Prefijo* (punto de venta) y el *Próximo número* para que coincidan
   con la primera hoja del talonario de la imprenta. Estos dos campos se piden en
   los dos modos.

Credits
=======

|company| |company_logo|
