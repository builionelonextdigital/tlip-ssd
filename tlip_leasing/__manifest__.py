{
    "name": "TLIP Leasing",
    "summary": """
    TLIP Leasing
    """,
    "description": """
        TLIP Leasing
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "tlip_stock",
        "tlip_account"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/ir_cron.xml",
        "data/income_fee_type_data.xml",
        "data/mail_template_data.xml",
        "views/leasing_rental_fee_views.xml",
        "views/leasing_quotation_views.xml",
        "views/reservation_agreement_views.xml",
        "views/lease_contract_views.xml",
        "views/supplemental_agreement_views.xml",
        "views/termination_agreement_views.xml",
        "views/contract_type_views.xml",
        "views/land_plot_views.xml",
        "views/stock_location_cr_views.xml",
        "views/res_partner_views.xml",
        "views/res_partner_cr_views.xml",
        "views/account_move_views.xml",
        "wizard/summary_change_wizard_views.xml",
        "views/menuitems.xml"
    ],
    "assets": {},
    "installable": True,
    "application": True,
    "auto_install": False
}
