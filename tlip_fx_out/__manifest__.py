# -*- coding: utf-8 -*-
{
    'name': "TLIP FX Out",
    'summary': "Multi-company daily FX out management with automatic calculation and cron jobs",
    'description': """
        Manage daily and monthly FX out rates per company and currency.
        Integrates into account.payment with fx_out, and provides
        automatic computation via button and scheduled cron jobs.
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Accounting',
    'license': 'LGPL-3',
    'version': '18.0.1.0.0',
    'depends': ['account', 'tlip_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/fx_out_rate_views.xml',
        'views/account_payment_views.xml',
        'views/accounting_period_closing_view_form.xml',
        'views/account_account_views.xml',
        'views/menus.xml',
        'data/fx_out_cron_monthly.xml',
    ],
    'installable': True,
    'application': True,
}
