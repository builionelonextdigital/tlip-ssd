from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    mysign_account_ids = fields.Many2many(
        comodel_name="mysign.account",
        relation="res_users_mysign_account_rel",
        column1="user_id",
        column2="account_id",
        string="MySign Accounts",
    )
