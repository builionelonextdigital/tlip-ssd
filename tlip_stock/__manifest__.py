{
    'name': "TLIP Stock",
    'summary': """
    TLIP Stock
    """,
    'description': """
        TLIP Stock
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Inventory',
    'license': 'LGPL-3',
    'version': '18.0.1.0.0',
    'depends': [
        'stock_account',
        'web_plan_layout',
        'tlip_account'
    ],
    'data': [
        # security
        "security/ir.model.access.csv",

        # data
        "data/function_data.xml",

        # views
        "views/product_category_views.xml",
        "views/land_plot_views.xml",
        "views/land_plot_category_views.xml",
        "views/land_plot_group_views.xml",
        "views/non_land_plot_item_views.xml",
        "views/product_manufacturer_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/stock_quant_views.xml",
        "views/tlip_stock_serial_views.xml",
        "views/account_asset_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_warehouse_views.xml",
        "views/stock_location_views.xml",
        "views/stock_quant_package_views.xml",

        # wizard
        "wizard/create_depreciation_wizard_views.xml",

        # menuitems
        "views/menuitems.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'tlip_stock/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False
}
