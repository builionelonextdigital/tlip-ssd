{
    'name': "PCV - VAS Trial Balance Report",

    'summary': """
            PCV - VAS Trial Balance Report
        """,
    'description': """
        PCV - VAS Trial Balance Report
    """,
    'category': 'Accounting',
    'version': '18.0.1.0',
    'author': "PCV",
    'depends': [
        'biz_vietnamese_accounting_menu', 'account_reports'
    ],
    "data": [
        # Security
        'security/ir.model.access.csv',
        'data/vas_trial_balance_report.xml',
        'data/account_report_action.xml',
        'view/account_account_views.xml',
        'view/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pcv_vas_trial_balance_report/static/src/components/account_report/header_name.xml',
            'pcv_vas_trial_balance_report/static/src/components/account_report/line_name.xml',
        ],
    },
    "license": "LGPL-3",
    'installable': True,
}
