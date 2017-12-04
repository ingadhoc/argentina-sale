# -*- coding: utf-8 -*-
{
    'name': 'Remito electrónico Argentino',
    'version': '9.0.1.0.0',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'ADHOC SA,Odoo Community Association (OCA)',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'depends': [
        'stock_voucher',  # por la clase receiptbooks y demas
        'delivery',
        'l10n_ar_account',
        'l10n_ar_afipws',
        # TODO sacar esta dependencia moviendo el campo de arba cit a otro mod.
        'l10n_ar_account_withholding',
    ],
    'external_dependencies': {
    },
    'data': [
        'wizards/arba_cot_wizard_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_book_view.xml',
        'views/product_template_view.xml',
        'views/product_uom_view.xml',
        'data/ir_sequence_data.xml',
        # 'security/invoice_sale_security.xml',
        # 'views/sale_view.xml',
        # 'views/res_company_view.xml',
        # 'res_config_view.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
