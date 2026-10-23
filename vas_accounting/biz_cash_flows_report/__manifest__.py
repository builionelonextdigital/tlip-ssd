# -*- coding: utf-8 -*-

{
    # Required
    "name": "BizApps - Cash Flows Report",

    # Information
    "version": "18.0.0.1",
    "application": True,
    "auto_install": False,
    "installable": True,
    "summary": """
        Cash Flow Report - New Version
    """,
    "description": "",
    "author": "support@bizapps.vn",
    "maintainer": "support@bizapps.vn",
    "contributors": ["support@bizapps.vn"],
    "website": "https://bizapps.vn/ung-dung",
    "sequence": 100,
    "license": "OPL-1",

    # Available packages
    "depends": ["base","biz_accounting_balance_sheet", "account", "account_accountant", "report_xlsx", "l10n_vn", "biz_vietnamese_accounting_menu"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/security.xml",
        # Data
        "data/cash_flows_data.xml",
        # Views
        "views/cash_flows_view.xml",
        "views/cash_flows_template_view.xml",
        "views/statements_cash_flows_report_view.xml",
        "views/res_config_settings_views.xml",
        "views/menuitems.xml",
        # Report
        "report/report_action.xml",
        "report/statements_cash_flows_template.xml",
    ],
}

