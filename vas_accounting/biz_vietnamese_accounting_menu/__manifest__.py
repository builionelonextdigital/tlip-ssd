# -- coding: utf-8 -*-
{
    # Required
    "name": "BizApps - Vietnamese Accounting Menu",

    # Information
    "category": "Hidden",
    "version": "18.0.0.1",
    "application": False,
    "auto_install": False,
    "installable": True,
    "post_load": None,
    "summary": "Thanh Menu Kế Toán Việt Nam",
    "description": "Thanh Menu Kế Toán Việt Nam",
    "author": "support@bizapps.vn",
    "maintainer": "support@bizapps.vn",
    "contributors": [],
    "website": "https://bizapps.vn/ung-dung",
    "sequence": 100,
    "license": "LGPL-3",

    # available packages
    "depends": ["account_accountant"],
    "data": [
        "views/menu.xml"
    ],
}