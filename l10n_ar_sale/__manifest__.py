{
    "name": "Argentinian Sale Total Fields",
    "version": "18.0.1.6.0",
    "category": "Localization/Argentina",
    "sequence": 14,
    "author": "ADHOC SA",
    "website": "www.adhoc.com.ar",
    "license": "AGPL-3",
    "summary": "",
    "depends": [
        "sale_ux",  # we make it dependent on sale_ux by setting group_delivery_date. More information in ticket 95265
        "l10n_ar_tax",
    ],
    "external_dependencies": {},
    "data": [
        "security/invoice_sale_security.xml",
        "views/sale_view.xml",
        "views/l10n_ar_sale_templates.xml",
        "views/sale_report_templates.xml",
        "wizards/res_config_settings_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}
