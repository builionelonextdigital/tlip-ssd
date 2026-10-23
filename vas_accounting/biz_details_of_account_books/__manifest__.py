# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Bizapps - Details of account books',
    'version': '18.0.0.1',
    'summary': 'A book of accounts',
    'description': """
Detailed book of accounts used for some accounts of the capital payment type without a separate book form.
The template is applicable to all forms of bookkeeping.
    """,
    'category': 'Accounting',
    'website': "http://www.bizapps.vn",
    'author': 'support@bizapps.vn',
    'depends': ['account_reports',],
    'data': [
        'data/report_data.xml',
        'views/detail_book_account.xml',
        'report/report_pdf_view.xml'
    ],
    "license": "OPL-1",
    'installable': True,
    'application': False,
    'auto_install': False,
}
