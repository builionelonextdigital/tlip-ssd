{
    'name': 'PC M-Invoice',
    'category': '',
    'summary': 'PC E-Invoice',
    'description': """
PC E-Invoice
    """,
    'version': '1.0',
    'license': 'LGPL-3',
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'depends': [
        'account',
        'mail',
        'web_widget_dropdown_dynamic',
        'web_widget_boolean_button'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',

        'data/ir_cron_data.xml',

        'views/minvoice_template_views.xml',
        'views/account_move_views.xml',
        'views/minvoice_account_views.xml',
        'views/account_journal_views.xml',

        'wizards/minvoice_action_wizard_view.xml',

        'menu/account_menu.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
