from odoo import api, fields, models
from collections import defaultdict


class BudgetLineYear(models.Model):
    _name = "budget.line.year"
    _description = "Budget Line Year"

    budget_year_id = fields.Many2one(
        comodel_name="budget.analytic.year",
        string="Budget Analytic Year",
        ondelete="cascade",
        index=True,
        required=True,
    )
    budget_code_id = fields.Many2one(related='account_id.budget_code_id')
    budget_department_id = fields.Many2one(related='account_id.budget_department_id')

    account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Code",
        ondelete="restrict",
        index=True,
        check_company=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="budget_year_id.company_id",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
    )
    planning_budget_amount = fields.Monetary(string="Report", compute="_compute_amount")

    budget_amount = fields.Monetary(
        compute="_compute_amount",
        string="Budget"
    )
    committed_amount = fields.Monetary(
        string="Reserved",
        compute="_compute_amount",
    )
    achieved_amount = fields.Monetary(
        string="Used",
        compute="_compute_amount",
    )
    remained_amount = fields.Monetary(
        string="Remained",
        compute="_compute_amount",
    )
    additional_amount = fields.Monetary(
        string="Additional",
        compute="_compute_amount",
    )

    def _compute_amount(self):
        budget_line_grouped = self._get_amount_by_grouped_budget()
        for rec in self:
            planning_budget, budget, committed, achieved, additional = budget_line_grouped.get(
                rec.account_id,
                (0, 0, 0, 0, 0),
            )
            rec.planning_budget_amount = planning_budget
            rec.budget_amount = budget
            rec.committed_amount = committed
            rec.achieved_amount = achieved
            rec.additional_amount = additional
            rec.remained_amount = budget + additional + achieved + committed

    def get_amount_by_grouped_account(
        self,
        budget_fields=[
            "budget_amount",
            "committed_amount",
            "achieved_amount",
            "additional_amount",
            "remained_amount",
        ],
    ):
        """Calculate and return total amount dict from provided budget_fields"""
        ### Result:
        # {'account_1': {'budget_amount': budget, 'committed_amount': committed, 'achieved_amount': achieved, 'additional_amount': additional, 'remained_amount': remained}, ...}
        line_grouped_account = {}
        for line in self:
            account = line.account_id
            line_grouped_account.setdefault(account, defaultdict(int))
            for field in budget_fields:
                line_grouped_account[account][field] += getattr(line, field, 0)

        return line_grouped_account

    def _get_amount_by_grouped_budget(self):
        # Return:
        # {(account_1, year_1): (budget, commit, achieved, additional), (account_2, year_1): (budget, commit, achieved, additional), ...}
        BudgetLine = self.env["budget.line"]
        read_group_res = BudgetLine._read_group(
            domain=[
                ("budget_analytic_id", "in", self.budget_year_id.monthly_line_ids.ids)
            ],
            groupby=["account_id"],
            aggregates=["id:recordset"],
        )
        return {
            account: (
                sum(budget_lines.mapped("planning_budget_amount")),
                sum(budget_lines.mapped("budget_amount")),
                sum(budget_lines.mapped("committed_amount")),
                sum(budget_lines.mapped("achieved_amount")),
                sum(budget_lines.mapped("additional_amount")),
            )
            for account, budget_lines in read_group_res
        }
