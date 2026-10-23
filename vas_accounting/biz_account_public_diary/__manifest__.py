{
    # Required
    "name": "BizApps - Account Public Diary",

    # Information
    "category": "Accounting/Accounting",
    "version": "18.0.0.1",
    "application": True,
    "auto_install": False,
    "installable": True,
    "summary": "",
    "description": "",
    "author": "support@bizapps.vn",
    "maintainer": "support@bizapps.vn",
    "contributors": ["support@bizapps.vn"],
    "website": "https://bizapps.vn/ung-dung",
    "sequence": 100,
    "license": "OPL-1",
    "pre_init_hook": "",
    "post_init_hook": "",
    "uninstall_hook": "",

    # Available packages
    "depends": ["base", "account", "account_reports"],
    "assets": {
        'web.assets_backend': [
            "biz_account_public_diary/static/src/js/action_account_public_diary.js"
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_public_diary_wizard_views.xml",
        "views/report_templates.xml",
    ],
}