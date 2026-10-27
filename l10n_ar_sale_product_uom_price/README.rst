.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

====================================================
Price per Product Unit with Argentinian VAT criteria
====================================================

Bridge between ``sale_product_uom_price`` and ``l10n_ar_sale``. It is installed on its own when
both are present.

``sale_product_uom_price`` shows the price of a line sold by packaging in the unit of the product,
on customer documents and on an optional column of the order lines. This module makes that price
follow the criteria of the Argentinian localization: without VAT when the customer discriminates
it, with VAT when it does not, the same way the printed quotation already does.

Installation
============

To install this module, you need to:

#. Nothing: it installs itself when ``sale_product_uom_price`` and ``l10n_ar_sale`` are both
   installed.

Configuration
=============

To configure this module, you need to:

#. Nothing to configure.

Usage
=====

#. The price is computed on the whole line and divided at the end, so quantity x unit price
   matches the subtotal of the report instead of a price rounded per unit.
#. The inverse used when the column is edited needs nothing here: ``sale_product_uom_price``
   derives it from this hook.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/ingadhoc/argentina-sale/issues>`_.
In case of trouble, please check there if your issue has already been reported.

Credits
=======

Authors
~~~~~~~

* ADHOC SA

Maintainer
~~~~~~~~~~

|company_logo|

This module is maintained by |company|.

To contribute to this module, please visit https://www.adhoc.com.ar.
