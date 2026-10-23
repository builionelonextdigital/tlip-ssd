{
    # Required
    "name": "BizApps - Balance sheet according to Circular No. 200",

    # Information
    "category": "",
    "version": "18.0.0.1",
    "application": True,
    "auto_install": False,
    "installable": True,
    "summary": "",
    "description": "Balance sheet according to Circular No. 200",
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
    "depends": [
        "account",
        "account_reports",
        "biz_account_counterpart"
    ],
    "data": [
        "views/account_group_views.xml",
        "views/report_templates.xml"
    ],
    "assets": {},
}