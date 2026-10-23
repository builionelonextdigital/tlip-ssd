{
    "name": "TLIP Account Report E-Sign",
    "summary": "Request E-Sign from accounting reports (P&L, Balance Sheet, Trial Balance, JE Detail)",
    "description": """
        Integrates Viettel MySign e-signing into the accounting report screens.
        Adds a 'Request E-Sign' button that generates a PDF and creates a Sign Ticket.
        Supports saving signer configurations as reusable Templates.
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "category": "Accounting",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "tlip_sign_ticket",
        "biz_profit_loss_statement",
        "biz_accounting_balance_sheet",
        "pcv_vas_trial_balance_report",
        "biz_details_of_account_books",
    ],
    "data": [
        "security/ir.model.access.csv",

        "views/sign_ticket_views.xml",
        "views/sign_document_type_views.xml",
        "views/accounting_balance_sheet_report_view.xml",
        "views/business_activities_results_view.xml",

        "views/menu_views.xml",

        "report/account_report_pdf_signer.xml",
        "report/detail_book_pdf_signer.xml",
        "report/account_balance_pdf.xml",
        "report/business_activities_results_pdf.xml",
    ],
    "assets": {
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
