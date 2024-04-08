from openupgradelib import openupgrade
import logging
logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    logger.info('Forzamos la actualización del template report_saleorder_document en módulo sale para que pueda aplicarse correctamente este fix https://github.com/ingadhoc/argentina-sale/pull/165')
    openupgrade.load_data(env.cr, 'sale', 'report/ir_actions_report_templates.xml')
    openupgrade.load_data(env.cr, 'l10n_ar_sale', 'views/sale_report_templates.xml')
