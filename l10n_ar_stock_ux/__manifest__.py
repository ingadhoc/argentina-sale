{
    "name": "Remitos, COT y demas ajustes de stock para Argentina",
    "version": "19.0.1.3.0",
    "category": "Localization/Argentina",
    "sequence": 14,
    "author": "ADHOC SA",
    "website": "www.adhoc.com.ar",
    "license": "AGPL-3",
    "depends": [
        "l10n_ar_stock",
        "l10n_ar_ux",
        "stock_picking_invoice_link",
        "stock_ux",
        # esta dependencia es solo por el campo declared value para:
        # a) reporte de remito
        # b) mandar valor declarado a wizard de COT
        # eventualmente se podría moer dicho campo a stock_ux y evitar esta dependencia
        "stock_declared_value",
    ],
    "data": [
        "security/res_groups.xml",
        "wizards/arba_cot_wizard_views.xml",
        "wizards/res_config_settings_view.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_type_views.xml",
        "views/product_template_views.xml",
        "views/uom_uom_views.xml",
        "views/stock_lot_views.xml",
        "views/report_deliveryslip.xml",
        "views/report_invoice.xml",
        "data/ir_sequence_data.xml",
        "data/product_uom_data.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [
        "demo/stock_picking_demo.xml",
    ],
    "installable": True,
    "auto_install": ["l10n_ar_stock"],
    "application": False,
}
