# -*- coding: utf-8 -*-
{
    'name': 'Viet Nam Address',
    'category': 'ALSW',
    'summary': 'Viet Nam Address',
    'description': """
Viet Nam Address
\t[*] District
\t[*] Ward
    """,
    'license': 'LGPL-3',
    'version': '1.0',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/res_country_district_data.xml',
        'data/res_country_ward_data.xml',
        'data/res_country_region_data.xml',
        'views/res_country_district_views.xml',
        'views/res_country_ward_views.xml',
        'views/res_country_state_views.xml',
        'views/res_country_region_views.xml',
        'views/res_partner_views.xml',
        'menu/menu.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
