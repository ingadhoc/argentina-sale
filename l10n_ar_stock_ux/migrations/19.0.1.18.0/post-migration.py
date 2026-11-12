import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Turn off the automatic delivery guide number on operation types without document type.

    The option is hidden in the form without a document type, so it could stay on after
    emptying that field. Validating did not number those transfers, but the option would come
    back already on if someone sets a document type later. Safe to run again.
    """
    cr.execute(
        """
        UPDATE stock_picking_type
           SET auto_assign_delivery_guide = FALSE
         WHERE auto_assign_delivery_guide
           AND l10n_ar_document_type_id IS NULL
        """
    )
    _logger.info("Automatic delivery guide number turned off on %s operation types without document type", cr.rowcount)
