{
    "name": "TLIP Utilities",
    "summary": """
    TLIP Utilities
    """,
    "description": """
        TLIP Utilities
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "tlip_account",
        "tlip_stock",
        "tlip_synchronization",
        "pcv_minvoice",
        "queue_job"
    ],
    "data": [
        "data/ir_cron_data.xml",
        "data/ir_sequence_data.xml",
        "data/queue_job_data.xml",
        "data/product_data.xml",
        "data/mail_template_data.xml",
        
        "security/security.xml",
        "security/ir.model.access.csv",

        "views/utilities_pricelist_views.xml",
        "views/account_move_views.xml",
        "views/electricity_category_views.xml",
        "views/electricity_kfactor_views.xml",
        "views/electricity_consumption_views.xml",
        "views/electricity_point_views.xml",
        "views/res_config_settings_views.xml",
        "views/water_consumption_views.xml",
        "views/water_point_views.xml",
        "views/invoice_type_views.xml",
        "views/account_move_line_views.xml",
        
        "wizards/utility_run_wizard_view.xml",

        "views/menuitem.xml",
        
        
    ],
    "assets": {},
    "installable": True,
    "application": True,
    "auto_install": False
}
