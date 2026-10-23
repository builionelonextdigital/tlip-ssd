from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BankExchangeRate(models.Model):
    _name = 'bank.exchange.rate'
    _description = 'Bank Exchange Rate'
    _order = 'date desc'

    currency_id = fields.Many2one(
        'res.currency', required=True,
        domain=lambda self: [('id', '!=', self.env.company.currency_id.id)])
    bank_id = fields.Many2one('res.bank', required=True, copy=False)
    date = fields.Date(required=True,
                       default=lambda self: fields.Date.context_today(self))
    selling_exchange_rate = fields.Float(
        string='Selling Exchange Rate',
        copy=False,
        required=True,
        digits=0,
        help="Selling Exchange Rate",
    )
    buying_exchange_rate = fields.Float(
        string='Buying Exchange Rate',
        copy=False,
        required=True,
        digits=0,
        help="Buying Exchange Rate",
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company.id,
        required=True, index=True,
        ondelete="cascade"
    )
    @api.constrains('currency_id', 'bank_id', 'date')
    def _constrains_unique_exchange_for_date(self):
        for rec in self:
            check_existed = self.search_count([
                ('currency_id', '=', rec.currency_id.id),
                ('bank_id', '=', rec.bank_id.id),
                ('date', '=', rec.date),
                ('id', '!=', rec.id),
                ('company_id', '=', rec.company_id.id)
            ])
            if check_existed > 0:
                raise UserError(
                    _(f'Bank {rec.bank_id.name}: Exchange Rate of {rec.currency_id.name} on {rec.date} already existed.'))

    @api.model
    def _get_exhange_rate(self, bank, date, currency, company):
        record = self.search([('bank_id', '=', bank.id),
                     ('date', '<=', date),
                     ('currency_id', '=', currency.id),
                     ('company_id', '=', company.id)], limit=1)
        if not record:
            record = self.search([('bank_id', '=', bank.id),
                                  ('currency_id', '=', currency.id),
                                  ('company_id', '=', company.id)], limit=1)
        return record
