from datetime import datetime

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from odoo.tools import SQL, float_compare, float_is_zero
from odoo.tools.date_utils import start_of, end_of
from odoo.exceptions import ValidationError


class AccountingPeriodClosing(models.Model):
    _name = 'accounting.period.closing'
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']
    _description = 'Accounting Period Closing'

    def _get_month_selection(self):
        return [(str(i), str(i).zfill(2)) for i in range(1, 13)]

    def _get_year_selection(self):
        current_year = fields.Datetime.now().year
        return [(str(i), str(i)) for i in range(current_year - 10, current_year + 11)]

    month = fields.Selection(
        selection=_get_month_selection, string="Month", required=True)
    year = fields.Selection(selection=_get_year_selection,
                            string="Year", required=True)

    name = fields.Char(compute="_compute_name",
                       string='Accounting Period', store=True)

    accounting_period = fields.Date(
        string='Select Period Date',
        compute='_compute_accounting_period',
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed')], string='Status',
        default='draft', required=True, tracking=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company.id,
        required=True, index=True,
        ondelete="cascade"
    )

    @api.constrains('name', 'company_id')
    def _constrains_name_unique(self):
        for record in self:
            if not record.name:
                continue
            duplicate_period_counts = record.search_count(
                [("name", "=", record.name), ("id", "!=", record.id), ('company_id', '=', record.company_id.id)]
            )
            if duplicate_period_counts > 0:
                raise UserError(
                    _(f"Period '{record.name}' already existed. Please select another period."))

    @api.depends('month', 'year')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.month and record.year:
                name = f"{(int(record.month)):02d}/{record.year}"
            record.name = name

    @api.depends('month', 'year')
    def _compute_accounting_period(self):
        for record in self:
            if record.month and record.year:
                record.accounting_period = end_of(fields.Date.to_date(
                    f"{record.year}-{(int(record.month)):02d}-01"), 'month')
            else:
                record.accounting_period = False

    @api.model
    def _calculate_book_exchange_rate(self, account, initial_data, from_date, to_date):
        AccountMoveLine = self.env['account.move.line']
        initial_balance = initial_data.get('balance')
        initial_amount_currency = initial_data.get('amount_currency')
        if account.internal_group in ('asset', 'expense'):
            indicator = -1
        else:
            indicator = 1
        select_items_query = SQL('''
            SELECT
                aml.id,
                aml.date,
                COALESCE((aml.amount_currency), 0.0) AS amount_currency,
                aml.balance
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            WHERE aml.account_id = %(account_id)s AND aml.date >= %(from_date)s AND aml.date <= %(to_date)s
                AND am.is_monthly_evaluation is not True AND aml.parent_state = 'posted'
            ORDER BY date, id''', account_id=account.id, from_date=from_date, to_date=to_date)
        self.env.cr.execute(select_items_query)
        lines = self.env.cr.dictfetchall()
        for line in lines:
            balance = line.get('balance')
            amount_currency = line.get('amount_currency')
            initial_balance += balance
            initial_amount_currency += amount_currency
            if float_compare(amount_currency * indicator, 0, 2):
                book_exchange_rate = round(
                    balance * indicator / amount_currency)
                move_line = AccountMoveLine.browse(line.get('id'))
                move_line.move_id.write(
                    {'book_exchange_rate': book_exchange_rate})
        return initial_balance, initial_amount_currency

    @api.model
    def _create_exchange_rate_diff_entry(self, initial_data, currency_rate,
                                         diff_balance, diff_amount_currency, date=None):
        company_id = initial_data.get('company_id')
        account_id = initial_data.get('account_id')
        currency_id = initial_data.get('currency_id')
        company = self.env['res.company'].browse(company_id)
        if not company:
            return
        journal = company.currency_exchange_journal_id
        expense_exchange_account = company.expense_currency_exchange_account_id
        income_exchange_account = company.income_currency_exchange_account_id
        move_vals = {
            'move_type': 'entry',
            'name': '/',
            'date': date or fields.Date.today(),
            'journal_id': journal.id,
            'line_ids': [],
            'always_tax_exigible': True,
            'is_monthly_evaluation': True
        }
        if diff_balance < 0:
            exchange_line_account = expense_exchange_account
            move_vals['entry_currency_rate'] = currency_rate
        else:
            exchange_line_account = income_exchange_account
            move_vals['book_exchange_rate'] = currency_rate
        currency = self.env['res.currency'].browse(currency_id)
        line_vals = [
            {
                'name': _(f'Exchange rate difference end of {self.name}'),
                'balance': diff_balance,
                'account_id': account_id,
                'company_id': company.id,
                'amount_currency': currency.round(diff_amount_currency),
                'currency_id': currency_id
            },
            {
                'name': _(f'Exchange rate difference end of {self.name}'),
                'account_id': exchange_line_account.id,
                'company_id': company.id,
                'balance': -diff_balance
            },
        ]
        move_vals['line_ids'] += [Command.create(vals) for vals in line_vals]
        exchange_move = self.env['account.move'].create(move_vals)
        exchange_move._post(soft=False)

    def _monthly_evaluation_foreign_currency(self):
        closing_accounts = self.env['account.account'].search([
            ('exchange_valuation_frequency', '=', 'monthly')
        ])
        if not closing_accounts:
            return
        from_date = start_of(self.accounting_period, 'month')
        to_date = end_of(self.accounting_period, 'month')
        for currency in self.env['res.currency'].search([]):
            initial_query = SQL('''
                SELECT
                    aml.account_id,
                    COALESCE(SUM(aml.amount_currency), 0.0) AS amount_currency,
                    aml.currency_id,
                    aml.company_id,
                    SUM(aml.balance) AS balance
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE aml.account_id in %(account_ids)s AND aml.date < %(from_date)s 
                    AND am.is_monthly_evaluation is not True AND aml.parent_state = 'posted' 
                    AND aml.company_id = %(company_id)s
                    AND aml.currency_id = %(currency_id)s
                GROUP BY aml.account_id, aml.currency_id, aml.company_id
                ''', account_ids=tuple(closing_accounts.ids), from_date=from_date, currency_id=currency.id, company_id=self.company_id.id)
            self.env.cr.execute(initial_query)
            closing_exchange_rate = self.env['bank.exchange.rate']._get_exhange_rate(bank=self.company_id.bank_exchange_rate_id,
                                                                                     date=to_date,
                                                                                     currency=currency,
                                                                                     company=self.company_id).buying_exchange_rate
            for initial_data in self.env.cr.dictfetchall():
                account = self.env['account.account'].browse(
                    initial_data['account_id'])
                ending_balance, ending_amount_currency = self._calculate_book_exchange_rate(
                    account, initial_data, from_date, to_date)
                closing_balance = closing_exchange_rate * ending_amount_currency
                diff_balance = round(closing_balance - ending_balance)
                diff_amount_currency = diff_balance / closing_exchange_rate
                if not float_is_zero(diff_balance, 2):
                    self._create_exchange_rate_diff_entry(
                        initial_data, closing_exchange_rate, diff_balance, diff_amount_currency, to_date)

    @api.model
    def _get_current_accounting_period(self):
        return self.search([('state', '=', 'open'), ('company_id', '=', self.env.company.id)], limit=1)

    def action_close(self):
        self.ensure_one()
        self._monthly_evaluation_foreign_currency()
        self.write({'state': 'closed'})

    def action_open(self):
        self.ensure_one()
        open_period = self.search_count([("state", "=", 'open')])
        if open_period > 0:
            raise ValidationError(_("You cannot open another period. Please close the previous period before opening new period"))
        self.write({'state': 'open'})

        moves = self.env['account.move'].search(
            [('is_monthly_evaluation', '=', True), ('reversed_entry_id', '=', False), ('company_id', '=', self.company_id.id)])
        moves._action_reverse()

    def validate_accounting_date(self, date):
        
        # A flag to skip this check
        if self.env.context.get('skip_accounting_period_check'):
            return True
        
        start_period_date = start_of(self.accounting_period, 'month')
        end_period_date = end_of(self.accounting_period, 'month')
        if date < start_period_date:
            raise ValidationError(_("You do not have permission to post entries outside the accounting period."))

    def action_oos_sync(self):
        self.ensure_one()
        company = self.company_id
        month = int(self.month)
        year = int(self.year)
        oos_entry_period = self
        salary_entries = self.env['account.move'].search(
            [('oos_entry_period_id', '=', oos_entry_period.id)])
        if any(salary_entry.state == 'posted' for salary_entry in salary_entries):
            raise ValidationError(
                _('The journal entry for salary has been recorded previously. Please unpost them if you want to sync again.'))
        # salary_entries.unlink()
        self.env['account.move']._run_oos_sync(
            company, month, year, oos_entry_period)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Notification",
                "message": 'The OOS data is syncing....',
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
