{
    "name": "TLIP Base",
    "summary": """
    TLIP Base
    """,
    "description": """
        TLIP Base
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "license": "LGPL-3",
    "version": "18.0.2.0.1",
    "depends": [
        "base",
        "contacts",
        "accountant",
        "analytic",
        "account_budget",
        "approvals",
        "dynamic_docx_pdf_reports_omax",
        "web_widget_dropdown_dynamic",
        "hr",
        "stock",
        "purchase",
        "vn_address",
        "web_plan_layout",
    ],
    "data": [
        # security
        "security/ir.model.access.csv",

        # data
        "data/partner_type_data.xml",
        "data/ir_sequence_data.xml",

        # views
        "views/res_partner_views.xml",
        "views/res_partner_cr_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_job_views.xml",
        
        # report
        "report/layout.xml",
        "report/report_action.xml",

        # wizard
        "wizard/document_preview_views.xml",
        "wizard/partner_summary_change_wizard_views.xml",
        "wizard/check_partner_exist_wizard_views.xml",
        "wizard/pdf_review_wizard_views.xml",

        # menu
        'views/menuitems.xml'
    ],
    "assets": {},
    "installable": True,
    "application": True,
    "auto_install": False
}
