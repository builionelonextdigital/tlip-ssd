import calendar
from datetime import datetime, date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.date_utils import get_month


class BudgetAllocationLine(models.Model):
    _name = "budget.allocation.line"
    _description = "Budget Allocation Line"

    allocation_id = fields.Many2one(
        comodel_name="budget.allocation.approval",
        required=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='allocation_id.company_id'
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id'
    )
    budget_analytic_id = fields.Many2one(
        comodel_name='budget.analytic',
        string='Monthly Budget',
        required=True,
        domain="[('id', 'in', available_budget_analytic_ids)]"
    )
    transfer_amount = fields.Float(digits=(16, 2), required=True)
    description = fields.Char('Description', required=True)
    available_budget_analytic_ids = fields.Many2many('budget.analytic', compute="_compute_available_budget_analytic_ids")

    @api.depends('allocation_id', 'allocation_id.date_from', 'allocation_id.date_to')
    def _compute_available_budget_analytic_ids(self):
        for record in self:
            record.available_budget_analytic_ids = record._get_available_budget_analytic_ids()

    def _get_available_budget_analytic_ids(self):
        """Get available budget analytics for a specific record"""
        self.ensure_one()
        allocation = self.allocation_id
        if not (allocation.date_from and allocation.date_to):
            return self.env['budget.analytic']

        confirmed_budget_year = allocation.confirmed_budget_year_id
        if not confirmed_budget_year:
            return self.env['budget.analytic']

        monthly_lines = confirmed_budget_year.monthly_line_ids
        existing_analytics = allocation.budget_allocation_line_ids.budget_analytic_id
        return (
            (monthly_lines - existing_analytics)
            .filtered(
                lambda analytic: analytic.date_from >= allocation.date_from
                and analytic.date_to <= allocation.date_to
            )
        )
