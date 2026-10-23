{
    "name": "PCV Sign Ticket",
    "summary": "Electronic Signature Ticket Management",
    "description": "Manage e-signature tickets and signer workflows via Viettel MySign.",
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "category": "Technical",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "mail",
    ],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "security/ir_rules.xml",

        "data/ir_sequence_data.xml",

        "views/sign_ticket_views.xml",
        "views/sign_document_type_views.xml",

        "wizards/sign_ticket_reject_wizard_views.xml",

        "views/menu_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
