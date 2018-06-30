{
    'name': 'Argentinian Sale Total Fields',
    'version': '11.0.1.0.0',
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
        'views/sale_view.xml',
        'wizards/res_config_settings_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
