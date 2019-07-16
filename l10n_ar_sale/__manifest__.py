{
    'name': 'Argentinian Sale Total Fields',
    'version': '12.0.1.0.0',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'sale',
        'l10n_ar_account',
    ],
    'external_dependencies': {
    },
    'data': [
        'security/invoice_sale_security.xml',
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'views/l10n_ar_sale_templates.xml',
        'views/sale_checkbook_views.xml',
        'wizards/res_config_settings_view.xml',
    ],
    'demo': [
    ],
    'installable': False,
    'auto_install': False,
    'application': False,
}
