from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    minvoice_account_id = fields.Many2one('minvoice.account', string='Tài khoản M-invoice')
