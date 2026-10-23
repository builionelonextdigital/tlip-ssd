{
    'name': "TLIP Account Asset",
    'summary': """
    TLIP Account
    """,
    'description': """
        TLIP Account Assset
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Accounting',
    'license': 'LGPL-3',
    'version': '18.0.1.0.0',
    'depends': [
        "tlip_account",
        "account_asset",
        "queue_job",
    ],
    'data': [
        # data
        "data/asset_revaluation_reason_data.xml",

        # views
        "views/account_asset_group_views.xml",
        "views/account_asset_views.xml",
        "views/account_deferred_revenue_views.xml",
        "views/account_deferred_expense_views.xml",
        "views/account_move_views.xml",
        "views/asset_modify_cr_views.xml",
        "views/asset_revaluation_reason_views.xml",
        "views/account_move_line_views.xml",

        # menu
        "views/menuitems.xml",

        # security
        "security/ir.model.access.csv",

        # wizard
        "wizard/asset_modify_views.xml",
        "wizard/asset_cancel_wizard_views.xml",
        "wizard/generate_asset_report_wizard_views.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
