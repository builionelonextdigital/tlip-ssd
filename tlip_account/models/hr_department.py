from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Department(models.Model):
    _inherit = "hr.department"

    code = fields.Char(string="Code", required=True, tracking=True)
    company_id = fields.Many2one(required=True)
    budget_department_id = fields.Many2one(
        "budget.department",
        string="Department",
        tracking=True,
    )

    @api.constrains("code", "company_id")
    def _constrains_code(self):
        for record in self:
            if not record.code:
                continue
            duplicate_code_counts = record.search_count(
                [("company_id", "=", record.company_id.id),
                 ("code", "=", record.code),
                 ("id", "!=", record.id)]
            )
            if duplicate_code_counts > 0:
                raise UserError(
                    _(f"Code '{record.code}' had existed. Please check again."))
