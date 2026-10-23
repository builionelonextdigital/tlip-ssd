from odoo import api, models, fields, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    legal_attoney_no = fields.Char()


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def get_accounting_manager_id(self, company_id=None):
        IrConfig = self.env['ir.config_parameter'].sudo()
        acc_department_code = IrConfig.get_param('accounting.department.code', 'ACC')
        domain = [('code', '=', acc_department_code)]

        if company_id:
            domain.append(('company_id', '=', company_id))

        acc_department = self.search(domain, limit=1)
        return acc_department.manager_id

