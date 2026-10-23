from odoo import api, fields, models, _
from odoo.exceptions import UserError

class BudgetDepartment(models.Model):
    _name = "budget.department"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Budget Department"

    name = fields.Char(required=True)
    code = fields.Char(required=True, tracking=True)
    job_id = fields.Many2one('hr.job', string='Position in Charge', compute='_compute_job_id')
    job_ids = fields.Many2many('hr.job', string='Position in Charge', required=True)
    budget_code_ids = fields.One2many(
        "account.analytic.account", "budget_department_id")
    count_budget_code = fields.Integer(compute="_compute_count_budget_code")
    department_group_id = fields.Many2one('budget.department.group')

    @api.constrains("code")
    def _constrains_code(self):
        for record in self:
            if not record.code:
                continue
            duplicate_code_counts = record.search_count(
                [("code", "=", record.code), ("id", "!=", record.id)]
            )
            if duplicate_code_counts > 0:
                raise UserError(
                    _(f"Code '{record.code}' already exists. Please check again.")
                )

    @api.depends("budget_code_ids")
    def _compute_count_budget_code(self):
        for rec in self:
            rec.count_budget_code = len(rec.budget_code_ids)

    @api.depends_context("company")
    def _compute_job_id(self):
        company = self.env["res.company"].browse(self._context.get("company_id")) if self._context.get("company_id") else self.env.company
        for rec in self:
            rec.job_id = rec.job_ids.filtered(lambda r: r.company_id == company)

    def action_view_budget_codes(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'analytic.action_account_analytic_account_form')
        action['domain'] = [('budget_department_id', '=', self.id)]
        action['context'] = {"default_budget_department_id": self.id}
        return action

    def copy(self, default=None):
        default = dict(default or {})
        default["name"] = _("%s (copy)", self.name)
        default["code"] = _("%s (copy)", self.code)
        return super().copy(default)
