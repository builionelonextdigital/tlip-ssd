from datetime import datetime, date

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.date_utils import get_month

class BudgetAnalyticYear(models.Model):
    _name = "budget.analytic.year"
    _description = "Budget Yearly"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Budget Yearly',
        required=True,
        tracking=True
    )
    fiscal_year_id = fields.Many2one('account.fiscal.year', required=True,
                                     tracking=True)
    state = fields.Selection(
        string="Status",
        selection=[
            ('draft', "Draft"),
            ('confirmed', "Open"),
            ('canceled', "Canceled"),
            ('done', "Done"),
        ],
        required=True, default='draft',
        readonly=True,
        copy=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    monthly_line_ids = fields.One2many(
        comodel_name='budget.analytic',
        inverse_name='budget_year_id',
        string='Budget Monthly',
        copy=False
    )
    budget_line_year_ids = fields.One2many(
        comodel_name='budget.line.year',
        inverse_name='budget_year_id',
        string='Budget Codes',
        copy=False
    )

    @api.model
    def get_current_budget_analytic_year(self):
        company = self.env.company
        return self.search([('state', '=', 'confirmed'), ('company_id', '=', company.id)], limit=1)

    def action_budget_draft(self):
        self.state = 'draft'

    def action_budget_cancel(self):
        self.state = 'canceled'

    def action_budget_confirm(self):
        self.ensure_one()
        self._validate_budget_analytic_year_confirm()
        budget_line_vals = self._prepare_budget_line_vals()
        self._action_generate_monthly_budget_periods(budget_line_vals)
        self._action_generate_budget_code(budget_line_vals)
        self._update_budget_reserved_dates()
        self.state = 'confirmed'

    def action_budget_done(self):
        self.state = 'done'

    def action_add_new_budget_code(self, analytic_accounts):
        budget_line_vals = self._prepare_budget_line_vals(analytic_accounts)
        self._action_generate_monthly_budget_periods(budget_line_vals)
        self._action_generate_budget_code(budget_line_vals)

    def _action_generate_monthly_budget_periods(self, budget_line_vals):
        if not self.monthly_line_ids:
            budget_vals = []
            for rec in self:
                budget_vals.extend(rec._prepare_monthly_budget_vals())
            self.env['budget.analytic'].create(budget_vals)

        self.monthly_line_ids.write({"budget_line_ids": budget_line_vals})

    def _action_generate_budget_code(self, budget_line_vals):
        self.write({"budget_line_year_ids": budget_line_vals})

    def _get_analytic_accounts(self, domain=[]):
        return self.env['account.analytic.account'].search(domain)

    def _prepare_budget_line_vals(self, analytic_accounts=None):
        # Return: budget.line and budget.line.year vals
        # Format: [(0, 0, {'account_id': act_id}), (0, 0, {'account_id': act_id}), ...]
        if not analytic_accounts:
            analytic_accounts = self._get_analytic_accounts(
                [("state", "=", "approved")])

        analytic_accounts = analytic_accounts.filtered(
            lambda account: account not in self.budget_line_year_ids.account_id)
        budget_lines = [(0, 0, {'account_id': account.id})
                        for account in analytic_accounts]
        return budget_lines

    def _prepare_monthly_budget_vals(self):
        self.ensure_one()
        if not self.fiscal_year_id:
            raise UserError(_("Please select Fiscal Year!"))

        budget_vals = []
        month_years = self.get_months_between(
            self.fiscal_year_id.date_from, self.fiscal_year_id.date_to)
        for month_year in month_years:
            date_from = date(month_year[1], month_year[0], 1)
            date_to = get_month(date_from)[1]
            budget_vals.append({
                'name': _('%s-%s' % (date_from.strftime('%b'), month_year[1])),
                'date_from': date_from,
                'date_to': date_to,
                'budget_type': 'both',
                'budget_year_id': self.id,
                'company_id': self.company_id.id
            })
        return budget_vals

    def get_months_between(self, start_date, end_date):
        current = start_date
        result = []

        while current <= end_date:
            result.append([current.month, current.year])
            # move to next month
            next_month = current.month % 12 + 1
            next_year = current.year if next_month > 1 else current.year + 1
            current = date(next_year, next_month, 1)

        return result

    def _validate_budget_analytic_year_confirm(self):
        budget_analytic_year = self.get_current_budget_analytic_year()
        if budget_analytic_year:
            raise UserError(_("You cannot open multiple budget yearly at once. Please contact your administrator for more information."))

    def _update_budget_reserved_dates(self):
        """Update existing budget_reserved records' dates to the beginning of budget year."""
        self.ensure_one()
        if not self.fiscal_year_id:
            return

        budget_year_start = self.fiscal_year_id.date_from
        budget_reserved_records = self.env['budget.reserved'].search([
            ('company_id', '=', self.company_id.id),
        ])

        if budget_reserved_records:
            budget_reserved_records.write({'date': budget_year_start})

    def open_import_budget_planning_wizard(self):
        self.ensure_one()
        return {
            'name': _('Import Budget Yearly Planning'),
            'res_model': 'import.budget.planning.wizard',
            'view_mode': 'form',
            'context': {
                'default_budget_analytic_year_id': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
