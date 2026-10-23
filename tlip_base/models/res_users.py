from odoo import models, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals):
        users = super(ResUsers, self).create(vals)
        users.partner_id.write({'internal_approval_state': True})
        return users
