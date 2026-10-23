# -*- coding: utf-8 -*-
{
    'name': 'Bizapps - Sales Invoice List',
    'version' : '18.0.0.1',
    'description': '',
    'category': 'Extra Tools',
    'website': "https://bizapps.vn/ung-dung",
    'author': "support@bizapps.vn",
    'company': 'Bizapps',
    "category": "",
    "license": "OPL-1",
    'depends': ['base', 'account', 'account_reports', 'report_xlsx','product'],
    'data': [
        'security/ir.model.access.csv',

        'report/report_view.xml',

        'wizard/wizard_sale_invoicelist_view.xml',

        'views/account_move_view.xml',
        'views/account_tax_view.xml',
        'views/account_view.xml',
        'views/product_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
