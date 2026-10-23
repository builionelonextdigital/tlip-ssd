import sys
sys.path.append('/opt/odoo/odoo-server')
import odoo
print(" ".join(odoo.service.db.list_dbs(True)))
