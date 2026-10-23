from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    budget_department_id = fields.Many2one('budget.department', string="Budget Department",
        compute='_compute_budget_department_id', search='_search_budget_department_id', store=False)

    @api.depends('employee_ids.department_id.budget_department_id')
    @api.depends_context('company')
    def _compute_budget_department_id(self):
        department_per_user = {
            employee.user_id: employee.department_id.budget_department_id
            for employee in self.env['hr.employee'].search([('user_id', 'in', self.ids), ('company_id', '=', self.env.company.id)])
        }
        for user in self:
            user.budget_department_id = department_per_user.get(user)
    
    def _search_budget_department_id(self, operator, value):
        return [('employee_ids.department_id.budget_department_id', operator, value)]