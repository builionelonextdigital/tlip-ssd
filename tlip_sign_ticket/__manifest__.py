{
    "name": "TLIP Sign Ticket",
    "summary": """
    TLIP Sign Ticket
    """,
    "description": """
        TLIP Sign Ticket
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "hr",
        "pcv_mysign",
        "tlip_approval",
    ],
    "data": [
        "views/hr_employee_views.xml",
        "views/res_company_views.xml",
        "views/sign_document_type_views.xml",
        "views/sign_ticket_views.xml",
    ],
    "assets": {},
    "installable": True,
    "application": True,
    "auto_install": False
}
