{
    "name": "Remito de Lote Preimpreso para Argentina",
    "version": "19.0.1.0.0",
    "category": "Localization/Argentina",
    "sequence": 14,
    "author": "ADHOC SA",
    "website": "www.adhoc.com.ar",
    "license": "AGPL-3",
    "summary": "Remito preimpreso en lotes: numera por las hojas del lote e imprime sin encabezado",
    "depends": [
        "l10n_ar_stock_picking_batch",
        "l10n_ar_stock_preprinted",
    ],
    "data": [
        "views/report_batch_deliveryslip.xml",
    ],
    "installable": True,
    "auto_install": True,
    "application": False,
}
