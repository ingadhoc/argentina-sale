{
    'name': 'Integracion entre modulo delivery y localización argentina',
    'version': '13.0.1.5.0',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'depends': [
        'delivery_ux',
        'l10n_ar_stock',
    ],
    'data': [
        'views/report_deliveryslip.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
