from odoo import models, fields

class AccountAccount(models.Model):
    _inherit = 'account.account'

    fx_currency_id = fields.Many2one(
        'res.currency',
        string="FX Currency",
        help="Foreign currency for reporting or evaluation."
    )
