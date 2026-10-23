{
    'name': "Stock Activities Report",

    'summary': """
            Stock Activities Report
        """,
    'description': """
        Stock Activities Report
    """,
    'category': 'Accounting',
    'version': '18.0.1.0',
    'author': "Portcities",
    'depends': [
        'stock'
    ],
    "data": [
        # Security
        'security/ir.model.access.csv',
        'wizards/inventory_report_activities_wizard.xml',
        'view/menu_views.xml'
    ],
    "license": "LGPL-3",
    'installable': True,
}
