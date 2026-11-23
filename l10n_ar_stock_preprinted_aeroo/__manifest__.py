{
    "name": "Remito Preimpreso con plantilla Aeroo",
    "version": "19.0.1.0.0",
    "category": "Localization/Argentina",
    "sequence": 14,
    "author": "ADHOC SA",
    "website": "www.adhoc.com.ar",
    "license": "AGPL-3",
    "summary": "Imprime el remito preimpreso con una plantilla .odt del cliente en vez del comprobante qweb",
    "depends": [
        "l10n_ar_stock_preprinted",
        "report_aeroo",
    ],
    "data": [
        "report/report_delivery_preprinted.xml",
        "views/stock_picking_type_views.xml",
    ],
    "installable": True,
    "auto_install": True,
    "application": False,
}
