{
    "name": "PCV MySign",
    "summary": "Viettel MySign Integration - Common Library",
    "description": "Common utilities, API endpoints, and error codes for Viettel MySign integration.",
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "category": "Technical",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "pcv_sign_ticket",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/mysign_config_rules.xml",

        "views/mysign_config_views.xml",
        "views/mysign_account_views.xml",
        "views/res_user_views.xml",
        "views/sign_ticket_views.xml",

        "views/menu_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pcv_mysign/static/src/components/mysign_popup.js",
            "pcv_mysign/static/src/components/mysign_popup.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
