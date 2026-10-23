from odoo import api, fields, models, _


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    bank_id = fields.Many2one('res.bank', required=True)
    account_ids = fields.Many2many(
        'account.account', relation="res_partner_bank_linked_account_rel",
        column1="partner_bank_id", column2="account_id", string='Linked Accounts')
    allow_in_payment = fields.Boolean(default=True, string='Receive Money')