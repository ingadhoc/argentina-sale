{
    "name": "Remitos, COT y demas ajustes de stock para Argentina",
<<<<<<< f241647b9ea0769c8c426b476e0d5cc11116f024
    "version": "19.0.1.12.0",
||||||| acf13eccef1790e667a9c9b15959546572dbe8e6
    "version": "19.0.1.17.0",
=======
    "version": "19.0.1.18.0",
>>>>>>> 4db9a724bdce9336888a3f775083823f1cc14a2d
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
        "views/ir_actions_report_views.xml",
        "views/report_deliveryslip.xml",
        "views/report_invoice.xml",
        "views/picking_templates.xml",
        "data/ir_sequence_data.xml",
        "data/product_uom_data.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [
        "demo/stock_picking_demo.xml",
    ],
    "installable": False,
    "auto_install": ["l10n_ar_stock"],
    "application": False,
}
