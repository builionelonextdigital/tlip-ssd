{
    'name': "TLIP Procurement",
    'summary': """
    TLIP Procurement
    """,
    'description': """
        TLIP Procurement
    """,
    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Procurement-Purchase',
    'license': 'LGPL-3',
    'version': '18.0.2.0.0',
    'depends': [
        "tlip_stock",
        "purchase_requisition",
        "tlip_account",
        "tlip_evaluation",
        "tlip_sign_ticket"
    ],
    'data': [
        # security
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "security/security.xml",

        # data
        "data/ir_sequence_data.xml",
        "data/ir_cron.xml",
        "data/product_category_data.xml",

        # views
        "views/res_partner_views.xml",
        "views/request_purchase_views.xml",
        "views/request_purchase_line_views.xml",
        "views/procurement_task_views.xml",
        "views/purchase_order_views.xml",
        "views/res_partner_cr_views.xml",
        "views/res_bank_views.xml",
        "views/res_config_settings_views.xml",
        "views/product_views.xml",
        "views/purchase_contract_type_views.xml",
        "views/purchase_contract_views.xml",
        "views/purchase_supplement_views.xml",
        "views/stock_picking_views.xml",
        "views/account_payment_views.xml",
        "views/checklist_template_views.xml",
        "views/res_config_settings_views.xml",
        "views/vendor_selection_rule_views.xml",
        "views/task_order_selection_views.xml",
        "views/product_template_views.xml",
        "views/account_move_views.xml",
        "views/contract_sign_rule_views.xml",
        "views/budget_reserved_views.xml",

        # wizard
        "wizard/import_einvoice_wizard_views.xml",
        "wizard/create_rfq_wizard_views.xml",
        "wizard/purchase_summary_change_wizard_views.xml",
        "wizard/task_rfq_confirm_wizard_views.xml",
        "wizard/periodical_survey_wizard_views.xml",
        "wizard/procurement_select_request_type_views.xml",
        "wizard/procurement_make_payment_view.xml",
        "wizard/stamp_final_contract_wizard_views.xml",

        # menuitems
        "views/menuitems.xml",

        # report
        "reports/vendor_evaluation_report.xml",
        "reports/purchase_quotation_templates.xml",
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'auto_install': False
}
