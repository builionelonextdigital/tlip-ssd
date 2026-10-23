from odoo import fields, models

class BudgetAnalytic(models.Model):
    _inherit = "budget.analytic"
    _description = "Budget Monthly"

    budget_year_id = fields.Many2one(
        comodel_name="budget.analytic.year",
        ondelete="cascade"
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id'
    )
    planning_budget_amount = fields.Monetary(string="Report", compute="_compute_amount")
    budget_amount = fields.Monetary(
        compute="_compute_amount",
        string="Budget"
    )
    committed_amount = fields.Monetary(
        string='Reserved',
        compute='_compute_amount',
    )
    achieved_amount = fields.Monetary(
        string='Used',
        compute='_compute_amount',
    )
    additional_amount = fields.Monetary(
        string="Additional",
        compute="_compute_amount"
    )
    remained_amount = fields.Monetary(
        string="Remained",
        compute="_compute_amount"
    )

    def _compute_amount(self):
        self.mapped('budget_line_ids')
        for rec in self:
            budget_lines = rec.budget_line_ids
            rec.achieved_amount = sum(budget_lines.mapped("achieved_amount"))
            rec.planning_budget_amount = sum(budget_lines.mapped("planning_budget_amount"))
            rec.budget_amount = sum(budget_lines.mapped("budget_amount"))
            rec.committed_amount = sum(budget_lines.mapped("committed_amount"))
            rec.additional_amount = sum(budget_lines.mapped("additional_amount"))
            rec.remained_amount = sum(budget_lines.mapped("remained_amount"))

    def open_budget_analytic(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'account_budget.act_budget_analytic_view')
        action.update({
            'views': [(self.env.ref('account_budget.view_budget_analytic_form').id, 'form')],
            'target': 'current',
            'res_id': self.id,
        })
        return action
