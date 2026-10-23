from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAccount(models.Model):
    _inherit = "account.account"

    exchange_valuation_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], string="Exchange Valuation Frequency")
    show_exchange_frequency = fields.Boolean(
        compute="_compute_show_exchange_frequency", store=False
    )
    bank_id = fields.Many2one('res.bank')
    use_for_cip = fields.Boolean(string="Use for CIP", default=False)

    @api.depends('currency_id', 'company_currency_id')
    def _compute_show_exchange_frequency(self):
        for rec in self:
            show = False
            if rec.currency_id and rec.currency_id != rec.company_currency_id:
                show = True
            rec.show_exchange_frequency = show
