from odoo import fields, models
from odoo.tools import groupby


class ResCompany(models.Model):
    _inherit = "res.company"

    bank_exchange_rate_id = fields.Many2one(
        comodel_name="res.bank",
        string="Default Bank Exchange Rate")
    deposit_percent_amount = fields.Float(string="Deposit Percent Amount")
    company_einvoice_url = fields.Char(string="eInvoice URL")
    invoice_mail_server_id = fields.Many2one('ir.mail_server')
    def _get_bank_account_info(self):
        self.ensure_one()
        vals = []
        ResPartnerBank = self.env['res.partner.bank'].sudo()
        bank_accounts = ResPartnerBank.search([('partner_id', '=', self.partner_id.id), ('allow_in_payment', '=', True)])
        for bank, accounts in groupby(bank_accounts.sorted(
                lambda line: (line.bank_id.id)),
                lambda line: (line.bank_id)):
            bank_accounts = ResPartnerBank.concat(*accounts)
            text = []
            for bank_account in bank_accounts:
                text += [f"{bank_account.acc_number} ({bank_account.currency_id.name})"]
            vals += [f"{', '.join(text)} at {bank.name}"]
        return vals
