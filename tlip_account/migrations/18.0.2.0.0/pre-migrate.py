def migrate(cr, version):
    cr.execute("""
        DROP TABLE procurement_select_request_type;
        DELETE FROM ir_model where model='procurement.select.request.type';
    """)
