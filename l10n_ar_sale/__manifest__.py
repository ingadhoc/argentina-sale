{
    'name': 'Argentinian Sale Total Fields',
<<<<<<< HEAD
    'version': "17.0.1.1.0",
||||||| parent of d825e92 (temp)
    'version': "16.0.1.6.0",
=======
    'version': "16.0.1.7.0",
>>>>>>> d825e92 (temp)
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'sale',
        'l10n_ar',
    ],
    'external_dependencies': {
    },
    'data': [
        'security/invoice_sale_security.xml',
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'views/l10n_ar_sale_templates.xml',
        'views/sale_checkbook_views.xml',
        'views/sale_report_templates.xml',
        'wizards/res_config_settings_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
