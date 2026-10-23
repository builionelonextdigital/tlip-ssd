{
    'name': 'Bizapps Account Counterparts',
    'version': '18.0.0.1',
    'category': 'Accounting',
    'summary': """""",
    'description': "",
    'author' : 'support@bizapps.vn',
    'website': 'https://www.bizapps.vn/ung-dung',
    'support': 'support@bizapps.vn',
    'depends': [
        'account',
        'account_reports',
        'biz_account_report_filter_account'
    ],
    'data': [
        "data/scheduler_data.xml",
        "security/ir.model.access.csv",
        "views/report_templates.xml",
        "views/account_move_line_ctp_views.xml",
        "views/account_move_line_view.xml",
        "views/account_move_view.xml",
        "wizard/wizard_account_counterpart_generator_views.xml",
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'OPL-1',
}
