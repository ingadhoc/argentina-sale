# -*- coding: utf-8 -*-
from openerp import models, fields
# from openerp.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class StockBook(models.Model):
    _inherit = 'stock.book'

    document_type_id = fields.Many2one(
        'account.document.type',
        'Document Type',
    )
