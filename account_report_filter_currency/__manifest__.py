# -*- coding: utf-8 -*-
{
    'name': 'Account Report Filter Currency',
    'category': 'Accounting/Accounting',
    'description': """
    """,
    'depends': [
        'account_reports'
    ],
    'data': [

        # View
        'views/account_report_views.xml',
    
    ],
    'assets': {
        'web.assets_backend': [
            'account_report_filter_currency/static/src/*',
        ],
    },
    'license': 'OEEL-1',
}
