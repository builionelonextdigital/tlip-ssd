# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Bizapps - Sổ tiền gửi ngân hàng (S08-DN)',
    'version': '18.0.0.1',
    'summary': 'Sổ tiền gửi ngân hàng (S08-DN)',
    'description': """
        Sổ tiền gửi ngân hàng (S08-DN)
    """,
    'category': 'Accounting',
    "website": "https://www.bizapps.vn",
    'author': 'support@bizapps.vn',
    'depends': ['biz_account_counterpart','account_reports','report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'report/bank_deposit_pdf_view.xml',
        'report/report_action.xml',

        'views/bank_deposit_book_view.xml'
    ],
    'installable': True,
    'application': False,
    "license": "OPL-1",
    'auto_install': False,
}
