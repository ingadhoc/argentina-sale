.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=======================================================================
Integración entre envío gratis de fidelización y localización argentina
=======================================================================

El módulo ``sale_loyalty_delivery`` arma la línea de recompensa de envío gratis heredando
los impuestos de la línea de flete del pedido, porque asume que el envío gratis descuenta
un flete ya cargado por un transportista.

Cuando el envío gratis se usa como promoción (por ejemplo por dominio de provincia) sobre
un pedido sin transportista, no hay línea de flete de la cual heredar el IVA: la línea de
recompensa nace sin impuestos y la validación ``check_vat_tax`` de ``l10n_ar_sale`` la
rechaza con el error "Debe haber un único impuesto del grupo de impuestos IVA por línea".

Este módulo toma, en ese caso, el IVA del propio producto de la recompensa mapeado por la
posición fiscal del pedido, tal como se obtendría agregando la línea a mano.

#. Solo aplica a compañías argentinas que requieren IVA (Responsable Inscripto).
#. La línea de recompensa nace en 0 igual que en el comportamiento estándar y se recalcula
   al elegir el transportista, por lo que los importes del pedido no cambian.

Installation
============

To install this module, you need to:

#. Only need to install the module

Configuration
=============

To configure this module, you need to:

#. Nothing to configure

Usage
=====

To use this module, you need to:

#. Crear un programa de fidelización con una recompensa de tipo "Envío gratis"
#. Aplicarlo sobre un pedido de venta sin método de envío seleccionado

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: http://runbot.adhoc.com.ar/

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ingadhoc/argentina-sale/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* |company| |icon|

Contributors
------------

Maintainer
----------

|company_logo|

This module is maintained by the |company|.

To contribute to this module, please visit https://www.adhoc.com.ar.
