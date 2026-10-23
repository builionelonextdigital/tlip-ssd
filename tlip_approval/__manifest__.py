{
    "name": "TLIP Approval",
    "summary": """
    TLIP Approval
    """,
    "description": """
        TLIP Approval
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "tlip_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/approval_security.xml",
        "views/approval_category_views.xml",
        "views/approval_request_views.xml",
        "views/approval_review_views.xml",
        "views/res_partner_views.xml",
        "views/res_partner_cr_views.xml",
        "views/mail_activity_views.xml",
        "wizard/submit_approval_wizard_views.xml",
        "wizard/withdraw_approval_wizard_views.xml"
    ],
    "assets": {},
    "installable": True,
    "application": True,
    "auto_install": False
}
