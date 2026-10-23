{
    "name": "TLIP Account",
    "summary": """
    TLIP Account
    """,
    "description": """
        TLIP Account
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "category": "Accounting",
    "license": "LGPL-3",
    "version": "18.0.2.0.0",
    "depends": [
        "account_accountant",
        "purchase",
        "stock",
        "tlip_approval",
        "tlip_sign_ticket",
        "pcv_minvoice",
        "report_xlsx",
        "queue_job",
        "l10n_vn",
        "biz_account_counterpart",
        "biz_vietnamese_accounting_menu"
    ],
    "data": [
        # security
        "security/ir.model.access.csv",
        "security/account_security.xml",

        # data
        "data/analytic_report_data.xml",
        "data/account_reports_data.xml",
        "data/cip_wip_report_data.xml",
        "data/ir_sequence_data.xml",
        'data/ir_cron_data.xml',
        "data/queue_job_data.xml",

        # views
        "views/hr_department_views.xml",
        "views/budget_category_views.xml",
        "views/budget_code_views.xml",
        "views/account_views.xml",
        "views/account_move_views.xml",
        "views/invoice_request_payment_views.xml",
        "views/account_payment_views.xml",
        "views/payment_request_payment_views.xml",
        "views/analytic_account_views.xml",
        "views/analytic_report_views.xml",
        "views/account_analytic_line_views.xml",
        "views/accounting_period_closing_views.xml",
        "views/budget_analytic_views.xml",
        "views/budget_analytic_year_views.xml",
        "views/bank_exchange_rate_views.xml",
        "views/res_bank_views.xml",
        "views/res_partner_bank_views.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        "views/budget_line_views.xml",
        "views/budget_line_year_views.xml",
        "views/budget_report_views.xml",
        "views/budget_allocation_approval_views.xml",
        "views/oos_mapping_views.xml",
        "views/oos_mapping_category_views.xml",
        "views/invoice_type_views.xml",
        "views/item_code_views.xml",
        "views/budget_department_views.xml",
        "views/budget_department_group_views.xml",
        "views/development_phase_views.xml",
        "views/development_project_views.xml",
        "views/uom_uom_views.xml",
        "views/batch_payment_views.xml",
        "views/res_company_views.xml",
        "views/account_move_line_views.xml",
        "views/budget_reserved_views.xml",
        "views/account_journal_views.xml",

        "report/report_power_2.1_template.xml",
        "report/report_power_2.2_template.xml",
        "report/report_power_1_template.xml",
        "report/report_power_2_template.xml",
        "report/report_power_3_template.xml",
        "report/report_power_4_template.xml",
        "report/report_water_template.xml",
        "report/report_other_turnover_template.xml",
        "report/report_other_request_template.xml",
        "report/report_land_rent_template.xml",
        "report/report_mf_rq_template.xml",
        "report/report_account_payment_template.xml",
        "report/report_batch_payment_template.xml",
        "report/ir_actions_report.xml",
        "report/account_payment_report.xml",
        "report/batch_payment_report.xml",

        # wizards
        "wizards/import_budget_planning_wizard_views.xml",
        "wizards/bank_reconciliation_report_wizard_views.xml",
        "wizards/monthly_overdue_report_wizard.xml",
        "wizards/debit_credit_report_wizard_views.xml",
        "wizards/salary_distribution_report_wizard_views.xml",

        # menuitems
        "views/account_menuitem.xml",

        # report
        "reports/bank_reconciliation_report_views.xml",
        "reports/salary_distribution_report_views.xml",
        "reports/payment_report_views.xml",
        "reports/debit_credit_control_list_report_views.xml",
        "reports/salary_distribution_xlsx_report_views.xml",
    ],
    "assets": {
        "web.assets_backend_lazy": [
            "tlip_account/static/src/js/pivot_view.js",
            "tlip_account/static/src/xml/pivot_view.xml",
        ],
        "web.assets_backend": [
            "tlip_account/static/src/css/cip_wip_report.css",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False
}
