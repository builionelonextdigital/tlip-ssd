{
    'name': "TLIP Account",
    'summary': """
    TLIP Access Rights
    """,
    'description': """
        TLIP Access Rights
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Accounting',
    'license': 'LGPL-3',
    'version': '18.0.1.0.0',
    'depends': [
        'sales_team', 'sale', 'tlip_utilities', 
        "tlip_procurement",
        "tlip_leasing",
        "tlip_stock",
    ],
    'data': [
        "security/security.xml",
        "security/procurement_security.xml",
        "security/budget_security.xml",
        "security/development_security.xml",
        "security/utility_security.xml",
        "security/account_payment_security.xml",
        "security/account_move_security.xml",
        "security/leasing_security.xml",
        "security/ir.model.access.csv",
        "views/menuitems.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'tlip_access_rights/static/src/js/lock_company_switch.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False
}
