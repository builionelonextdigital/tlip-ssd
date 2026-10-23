from odoo import api, fields, models, _
from odoo.tools import SQL
from odoo.exceptions import ValidationError


class BankReconciliationReport(models.TransientModel):
    _name = 'bank.reconciliation.report'
    _description = "Bank Reconciliation Report"

    name = fields.Char(compute='_compute_name', store=True)
    partner_bank_id = fields.Many2one('res.partner.bank', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)
    date = fields.Date(readonly=True)
    account_id = fields.Many2one('account.account', string='Linked Account',
                                 readonly=True)
    buying_exchange_rate = fields.Float(
        compute='_compute_exchange_rate', string='EXR-TTB')
    selling_exchange_rate = fields.Float(
        compute='_compute_exchange_rate', string='EXR-TTS')
    total_per_book = fields.Float(string='Per Book', readonly=True)
    total_per_bank = fields.Float(string='Per Bank')
    amount_diff = fields.Float(
        string='Difference', compute='_compute_amount_diff')
    amount_equivalent = fields.Float(
        string='Equivalent', compute='_compute_amount_equivalent')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', readonly=True)

    @api.depends('partner_bank_id', 'partner_bank_id.bank_id')
    def _compute_name(self):
        for rec in self:
            partner_bank = rec.partner_bank_id
            bank = partner_bank.bank_id
            rec.name = f'{bank.name} - {partner_bank.partner_id.name} ({partner_bank.acc_number})'

    @api.depends('date', 'partner_bank_id.bank_id')
    def _compute_exchange_rate(self):
        for rec in self:
            exchange_rate = self.env['bank.exchange.rate'].search(
                [('bank_id', '=', rec.partner_bank_id.bank_id.id),
                 ('date', '<=', rec.date),
                 ('currency_id', '=', rec.currency_id.id)], limit=1)
            exr_sale, exr_buy = 1.0, 1.0
            if exchange_rate:
                exr_sale, exr_buy = exchange_rate.selling_exchange_rate, exchange_rate.buying_exchange_rate
            rec.selling_exchange_rate = exr_sale
            rec.buying_exchange_rate = exr_buy

    @api.depends('total_per_bank')
    def _compute_amount_diff(self):
        for rec in self:
            rec.amount_diff = rec.total_per_book - rec.total_per_bank

    @api.depends('total_per_book', 'selling_exchange_rate')
    def _compute_amount_equivalent(self):
        for rec in self:
            amount_equivalent = rec.total_per_book
            if rec.currency_id != rec.company_id.currency_id:
                amount_equivalent *= rec.selling_exchange_rate
            rec.amount_equivalent = amount_equivalent

    @api.model
    def _query_to_select_data(self, date=fields.Date.today(), partner_bank_ids=[]):
        query = SQL('''
            SELECT
                partner_bank.id AS partner_bank_id,
                line.account_id,
                line.company_id,
                SUM(line.amount_currency) as total_per_book,
                SUM(line.amount_currency) as total_per_bank,
                line.currency_id AS currency_id,
                %(date)s as date
            FROM res_partner_bank partner_bank
                LEFT JOIN res_partner_bank_linked_account_rel bank_account on bank_account.partner_bank_id = partner_bank.id
                LEFT JOIN account_account account ON account.id = bank_account.account_id
                LEFT JOIN account_move_line line ON line.account_id = account.id
                LEFT JOIN res_partner partner ON partner.id = line.partner_id
                LEFT JOIN res_currency currency ON currency.id = line.currency_id
            WHERE line.date <= %(date)s and partner_bank.id in %(partner_bank_ids)s
            GROUP BY partner_bank.id, line.account_id, line.company_id, line.currency_id
            ''', date=date, partner_bank_ids=tuple(partner_bank_ids))
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall() or []

    def _generate_reconciliation_data(self, date=fields.Date.today(), partner_bank_ids=[]):
        datas = self._query_to_select_data(date, partner_bank_ids)
        if not datas:
            raise ValidationError(
                _('Cannot find any data that related to selected Bank Accounts.'))
        records = self.create(datas)
        return {
            'name': _('Bank Reconciliation Report'),
            'res_model': self._name,
            'view_mode': 'list',
            'context': {
                'create': 0,
                'delete': 0,
                'search_default_group_by_name': 1
            },
            'target': 'current',
            'domain': [('id', 'in', records.ids)],
            'type': 'ir.actions.act_window',
        }
