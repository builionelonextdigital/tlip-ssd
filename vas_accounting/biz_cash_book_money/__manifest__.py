# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Bizapps - Cash book money',
    'version': '18.0.0.1',
    'summary': 'Cash book money',
    'description': """
        Cash book money
    """,
    'category': 'Accounting',
    "website": "https://www.bizapps.vn",
    'author': 'support@bizapps.vn',
    'depends': ['account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'data/cash_book.xml',
        'report/report_pdf_view.xml',
        'views/cash_book.xml'
    ],
    'installable': True,
    'application': False,
    "license": "OPL-1",
    'auto_install': False,
}
