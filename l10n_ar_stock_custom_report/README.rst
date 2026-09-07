.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

======================================
Plantilla Propia del Remito Argentino
======================================

Permite que un tipo de operación imprima su remito con una **plantilla QWeb
propia**, en lugar del comprobante estándar de ``l10n_ar_stock_ux``.

El módulo no trae ninguna plantilla: trae el campo y su validación. La plantilla
la crea un consultor funcional o el propio cliente desde *Ajustes > Técnico >
Vistas* — sin módulo y sin deploy — o llega como data de otro módulo. Vacío el
campo, no cambia absolutamente nada.

Para qué sirve
==============

Hay dos personalizaciones del remito que aparecen en clientes reales, y el campo
cubre las dos:

* **Formato** — el talonario de cada imprenta trae su propia grilla, y el
  comprobante estándar no siempre cae donde el papel lo espera. Se resuelve con
  una plantilla dibujada desde cero para ese papel.
* **Campos** — el cliente necesita datos que el comprobante no trae por defecto,
  pero el formato nuestro le sirve. Se resuelve con una vista que hereda el
  comprobante estándar y le agrega los campos.

Qué agrega
==========

* ``stock.picking.type.l10n_ar_delivery_report_view_id`` (opcional): la vista
  QWeb con la que se imprime el remito de ese tipo de operación. Una restricción
  de servidor exige que sea una vista QWeb de modo ``primary`` (la vista sola no
  cubre imports ni escrituras por ORM).
* ``stock.picking._get_name_delivery_report`` devuelve el ``key`` de esa vista.
  Es el key y no el external id porque el ``t-call`` resuelve los templates por
  ``ir.ui.view.key``, y una vista creada desde la interfaz no tiene external id.

Cómo se arma la plantilla
=========================

**Formato (plantilla desde cero).** Una vista QWeb con un ``<t t-name="...">``
propio, que recibe la transferencia en la variable ``o`` y el tipo de copia en
``copy_type``, y abre con ``<t t-call="web.html_container">`` igual que el
comprobante estándar.

Ojo: una plantilla desde cero no imprime nada que no dibuje. En autoimpreso eso
significa que el encabezado, el número y el CAI corren por cuenta de la
plantilla; en preimpreso es justamente lo que se busca, porque ya vienen impresos
en el papel.

**Campos (herencia del comprobante).** Una vista de modo ``primary`` con
``inherit_id`` al comprobante estándar
(``l10n_ar_stock_ux.report_delivery_document``) y los xpaths que agregan los
campos. Odoo sube por la herencia y aplica el diff sobre el arch del padre, así
que el formato, el encabezado, el número y el CAI se conservan.

Lo que **no** se acepta es una vista de modo ``extension``: no tiene arch
renderizable propio — es un diff de xpaths — así que el ``t-call`` imprimiría
los nodos del diff sueltos en vez del remito.

Configuración
=============

En *Inventario > Configuración > Tipos de operación*, para un tipo de operación
de salida:

#. Definir el *Tipo de documento* de remito.
#. Crear la vista QWeb desde *Ajustes > Técnico > Vistas*, con uno de los dos
   criterios de arriba.
#. Seleccionarla en *Plantilla del Remito*.

Advertencia sobre las actualizaciones de versión
================================================

Una plantilla creada en la base no está en el repositorio, así que no la cubre la
actualización estándar de versión. Las dos formas de armarla no corren el mismo
riesgo:

* Una plantilla **desde cero** solo depende de ``web.html_container`` y de los
  campos que lee: aguanta bien un cambio de versión.
* Una plantilla **heredada** depende de la estructura del comprobante estándar.
  Si un nodo se mueve, el xpath deja de aplicar y la vista se rompe. Conviene
  revisarla en cada actualización.

Credits
=======

|company| |company_logo|
