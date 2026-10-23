from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    locked_requisitions = env['purchase.requisition'].search([('state', '=', 'locked')])
    tasks = locked_requisitions.task_ids | locked_requisitions.task_id
    tasks.write({'is_locked': True})
