{
    'name': "Plan Layout View",
    'summary': """
    Plan Layout View
    """,
    'description': """
    Plan Layout View
    """,
    'license': 'LGPL-3',
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Web',
    'version': '18.0.1.0.0',
    'depends': [
        'web'
    ],
    'assets': {
        'web.assets_backend': [
            'web_plan_layout/static/src/views/**/*',
        ],
        'web.qunit_suite_tests': [
            'web_plan_layout/static/src/lib/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False
}
