.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=======================================
Plantilla Propia del Remito Preimpreso
=======================================

Permite que un tipo de operación con remito **preimpreso** lo imprima con una
**plantilla QWeb propia**, en lugar del comprobante estándar de
``l10n_ar_stock_ux``.

El módulo no trae ninguna plantilla: trae el campo y su validación. La plantilla
la crea un consultor funcional o el propio cliente desde *Ajustes > Técnico >
Vistas* — sin módulo y sin deploy — o llega como data de otro módulo. Vacío el
campo, no cambia absolutamente nada.

Reemplaza el camino anterior, que era un reporte aeroo sustituyendo el nuestro
con ``report_substitute``: un módulo descartado en 19, que además cobraba líneas
de personalización. Este módulo es producto soportado y la plantilla creada en
base no cuenta líneas.

El módulo **no** es auto-instalable: se instala solo en las bases donde el
cliente tiene la perso. El estándar sigue siendo nuestro remito.

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

Alcance: solo preimpreso
========================

La plantilla propia se aplica **solo** cuando el *Modo de Impresión del Remito*
del tipo de operación es *Preimpreso*, y el campo se muestra solo en ese modo.

Es una decisión deliberada, no un límite del mecanismo. El hook y la validación
sirven igual en autoimpreso: una vista ``primary`` que hereda el comprobante
estándar conserva encabezado, número y CAI, así que el caso "agregar campos"
funcionaría tal cual. No se abre porque hoy no hay demanda de perso en
autoimpreso, y porque una plantilla dibujada desde cero en autoimpreso saldría
sin número y sin CAI sobre papel en blanco — ahí sí haría falta un aviso al
guardar, que con el caso cerrado no hace falta.

Dos consecuencias prácticas:

* El cliente que pasa de preimpreso a remito digital no tiene que borrar la
  plantilla: deja de verla y deja de aplicarse.
* El día que aparezca demanda de perso en autoimpreso, se saca la condición del
  hook, se abre la visibilidad del campo y se define ahí el aviso al guardar.

Cómo se arma la plantilla
=========================

**Formato (plantilla desde cero).** Una vista QWeb con un ``<t t-name="...">``
propio, que recibe la transferencia en la variable ``o`` y el tipo de copia en
``copy_type``, y abre con ``<t t-call="web.html_container">`` igual que el
comprobante estándar.

Ojo: una plantilla desde cero no imprime nada que no dibuje. En preimpreso es
justamente lo que se busca, porque el encabezado, el número y el CAI ya vienen
impresos en el papel de la imprenta.

**Campos (herencia del comprobante).** Una vista de modo ``primary`` con
``inherit_id`` al comprobante estándar
(``l10n_ar_stock_ux.report_delivery_document``) y los xpaths que agregan los
campos. Odoo sube por la herencia y aplica el diff sobre el arch del padre, así
que se conserva el formato nuestro, con el encabezado y el pie que el preimpreso
deja en blanco.

Lo que **no** se acepta es una vista de modo ``extension``: no tiene arch
renderizable propio — es un diff de xpaths — así que el ``t-call`` imprimiría
los nodos del diff sueltos en vez del remito.

Configuración
=============

En *Inventario > Configuración > Tipos de operación*, para un tipo de operación
de salida:

#. Definir el *Tipo de documento* de remito.
#. Poner el *Modo de Impresión del Remito* en *Preimpreso*
   (``l10n_ar_stock_preprinted``).
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
