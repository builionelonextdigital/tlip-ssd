from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BudgetDepartmentGroup(models.Model):
    _name = "budget.department.group"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Budget Department Group"

    name = fields.Char(required=True)
    budget_department_ids = fields.One2many(
        "budget.department",
        "department_group_id",
        string="Departments",
    )
    job_id = fields.Many2one('hr.job', string='Position in Charge', compute='_compute_job_id')
    job_ids = fields.Many2many('hr.job', string='Position in Charge', required=True)

    @api.constrains("name")
    def _constrains_name(self):
        for record in self:
            if not record.name:
                continue
            duplicate_name_counts = record.search_count(
                [
                    ("name", "=", record.name),
                    ("id", "!=", record.id),
                ]
            )
            if duplicate_name_counts > 0:
                raise UserError(
                    _(
                        f"{record._name} '{record.name}' already exists. Please check again."
                    )
                )

    def _compute_job_id(self):
        company = self.env["res.company"].browse(self._context.get("company_id")) if self._context.get("company_id") else self.env.company
        for rec in self:
            rec.job_id = rec.job_ids.filtered(lambda r: r.company_id == company)

    def copy(self, default=None):
        default = dict(default or {})
        default["name"] = _("%s (copy)", self.name)
        return super().copy(default)
