.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=============================================
Argentinean Delivery Guides on Batch Pickings
=============================================

Extends batch pickings to support Argentine delivery guides (remitos).

Main features:

* **Generate delivery guide from a batch**: a *Generate Delivery Guide* button appears on the batch form once it is validated (state ``done``) and the operation type has an Argentine document type configured. It creates the guide on the first picking and propagates the number and CAI data to all other pickings in the batch.
* **Synchronisation**: the delivery guide number on the batch is computed from its pickings and kept in sync. Editing it on the batch writes back to all pickings (only those that differ are updated).
* **View protection**: on pickings that belong to a batch the delivery guide number field becomes read-only, preventing out-of-sync manual edits.
* **Declared value**: the batch aggregates the declared value from its pickings.

Installation
============

To install this module, you need to:

#. Only need to install the module

Configuration
=============

To configure this module, you need to:

#. Nothing to configure


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: http://runbot.adhoc.com.ar/

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ingadhoc/stock/issues>`_. In case of trouble, please
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
