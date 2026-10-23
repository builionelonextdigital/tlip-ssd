{
    "name": "TLIP Evaluation",
    "summary": """
    TLIP Evaluation
    """,
    "description": """
        TLIP Evaluation
    """,
    "author": "Port Cities",
    "website": "http://www.portcities.net",
    "license": "LGPL-3",
    "version": "18.0.1.0.0",
    "depends": [
        "tlip_approval"
    ],
    "data": [
        # security
        "security/ir.model.access.csv",

        # views
        "views/evaluation_criteria_views.xml",
        "views/evaluation_question_views.xml",
        "views/evaluation_survey_views.xml",
        "views/evaluation_survey_criteria_views.xml",
        "views/res_partner_views.xml",

        # menu
        'views/menuitems.xml'
    ],
    "assets": {},
    "installable": True,
    "application": True,
    "auto_install": False
}
