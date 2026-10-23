# -*- coding: utf-8 -*-
{
    'name': 'Debt Currency Report',
    'category': 'Accounting/Accounting',
    'description': """
""",
    'depends': [
        'account_report_filter_currency', 
        'biz_account_report_filter_account'
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/account_debt_report_data.xml',
        'data/account_debt_report_action.xml',
        # Wizard
        # View
        # Menu
        'menu/menu.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'vas_debt_report/static/src/xml/*',
        ],
    },
    'license': 'OEEL-1',
}
