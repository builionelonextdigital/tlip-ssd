# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Bizapps - Filter account report',
    'version': '18.0.0.1',
    'summary': 'Add filter account to accounts report',
    'description': """
Add filter account to accounts report
    """,
    'category': 'Accounting',
    'website': "http://www.bizapps.vn",
    'author': 'support@bizapps.vn',
    'depends': ['account_reports'],
    'data': [
        'views/account_report_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'biz_account_report_filter_account/static/src/xml/*',
        ],
    },
    'installable': True,
    "license": "OPL-1",
    'application': False,
    'auto_install': False,
}
