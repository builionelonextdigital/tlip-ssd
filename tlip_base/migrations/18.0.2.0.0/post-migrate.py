from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Remove xsd validation crons as the validation is done differently.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.partner'].search([('user_ids', '=', False), ('internal_approval_state', '=', False)]).write({'internal_approval_state': True})
