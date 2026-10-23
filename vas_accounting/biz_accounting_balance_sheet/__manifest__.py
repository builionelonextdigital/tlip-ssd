# -*- coding: utf-8 -*-
{
    # Required
    "name": "BizApps - Accounting Balance Sheet",

    # Information
    "version": "18.0.0.1",
    "application": True,
    "auto_install": False,
    "installable": True,
    "summary": "",
    "description": "biz_accounting_balance => biz_accounting_balance_sheet",
    "author": "support@bizapps.vn",
    "maintainer": "support@bizapps.vn",
    "contributors": ["support@bizapps.vn"],
    "website": "https://bizapps.vn/ung-dung",
    "sequence": 100,
    "license": "OPL-1",

    # Available packages
    "depends": ["base", "account", "account_accountant", "report_xlsx", "l10n_vn", "biz_vietnamese_accounting_menu"],
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/security.xml",
        # Data
        "data/accounting_balance_sheet_data_A.xml",
        "data/accounting_balance_sheet_data_B.xml",
        "data/accounting_balance_sheet_data_C.xml",
        "data/accounting_balance_sheet_data_D.xml",
        # Report
        "reports/action_report.xml",
        "reports/account_balance_pdf.xml",
        # Views
        "views/accounting_balance_sheet_view.xml",
        "views/accounting_balance_template_view.xml",
        "views/accounting_balance_sheet_report_view.xml",
        "views/res_config_settings_views.xml",
        "views/menuitems.xml"
    ],
}
