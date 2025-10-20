.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===================================================
Argentina - Stock Delivery Integration
===================================================

This module integrates the delivery functionality with the Argentinian localization features, providing enhanced delivery slip reports and ARBA COT (Código de Operaciones de Traslado) wizard integration for stock movements.

Features
========

#. **Enhanced Delivery Slip Reports**: Adds delivery-specific information to delivery documents including:
   
   * Package weight and weight unit of measure
   * Carrier tracking reference numbers
   * Detailed carrier information (name, VAT number, and address)
   * Integration with Argentinian identification document types

#. **ARBA COT Wizard Integration**: Extends the ARBA COT (Transport Operations Code) wizard to automatically pre-fill the carrier partner information when accessed from stock picking operations.

Installation
============

To install this module, you need to:

#. Install the module from the Apps menu
#. The module will be automatically installed when both ``delivery_ux`` and ``l10n_ar_stock_extended`` modules are present

Configuration
=============

To configure this module, you need to:

#. Configure your delivery carriers in Inventory > Configuration > Delivery > Delivery Methods
#. Ensure your carriers have proper partner information including VAT numbers and addresses
#. The module will automatically enhance delivery reports with the configured information

Usage
=====

To use this module:

#. **Enhanced Delivery Reports**: When printing delivery slips, the reports will automatically include:
   
   * Weight information if configured on the picking
   * Tracking references from the carrier
   * Complete carrier details including identification documents

#. **ARBA COT Integration**: When using the ARBA COT wizard from stock pickings, the carrier partner will be automatically selected based on the picking's carrier configuration.

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
