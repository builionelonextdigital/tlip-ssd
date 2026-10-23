from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from ..tools.import_helper import read_xlsx

class ImportBudgetPlanningWizard(models.TransientModel):
    _name = 'import.budget.planning.wizard'
    _description = 'Import Budget Planning Wizard'

    import_file = fields.Binary(string='Import File', required=True)
    filename = fields.Char()
    budget_analytic_year_id = fields.Many2one('budget.analytic.year', required=True)
    message = fields.Text()
    imported = fields.Boolean()
    type = fields.Selection([('report', 'Report Purpose'),
                             ('budget', 'Budget Purpose')], required=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    def button_import(self):
        """
            row_datas[0]: Title
            row_datas[1]: Budget Period from col 2 (1)
            from row_datas[2]: Budget Planning data
            - row_data[0]: Dept Code
            - row_data[1]: Budget Code
            - from row_data[2]: budget of each period

        """
        budget_periods = self.budget_analytic_year_id.monthly_line_ids
        sheet, row_datas = read_xlsx(self.import_file)
        failed = 0
        success_code, error_msgs = [], []
        index = 2
        budget_matching = {}
        index_period = 0
        for index_period in range(0, 12):
            budget_matching.update({index: budget_periods[index_period].id})
            index += 1
        budget_code_recs = self.env['budget.code'].sudo().search([])
        analytic_accounts = self.env['account.analytic.account'].sudo().search([('active', '=', True)])
        for row_data in row_datas[2:]:
            department_code = row_data[0]
            budget_code = row_data[1]
            import logging
            logging.info(budget_code)
            if not budget_code:
                break
            budget_code_rec = budget_code_recs.filtered(lambda r: r.code == budget_code)
            if not budget_code_rec:
                continue

            complete_code = f"{department_code}-{budget_code}"
            analytic_account = analytic_accounts.filtered_domain([('complete_code', '=', complete_code),('company_id','=', self.company_id.id)])
            if not analytic_account:
                department_rec = self.env['budget.department'].search([('code', '=', department_code)], limit=1)
                analytic_account = self.env['account.analytic.account'].with_context(bypass_approval=True).create({'budget_code_id': budget_code_rec.id,
                                                                                                            'code': complete_code,
                                                                                                            'name': budget_code_rec.name,
                                                                                                            'company_id': self.company_id.id,
                                                                                                            'budget_category_id': budget_code_rec.budget_category_id.id,
                                                                                                            'default_account_ids': [(6, 0, budget_code_rec.default_account_ids.ids)],
                                                                                                            'budget_department_id': department_rec.id})
            self.budget_analytic_year_id.action_add_new_budget_code(analytic_account)
            budget_lines = self.env['budget.line'].search([('account_id', '=', analytic_account.id)])
            index = 1
            for budget_amount in row_data[2:]:
                index += 1
                if not budget_amount:
                    continue
                try:
                    budget_amount = float(budget_amount)
                except:
                    budget_amount = 0
                budget_analytic_id = budget_matching.get(index, False)
                if not budget_analytic_id:
                    continue
                budget_line = budget_lines.filtered(lambda l: l.budget_analytic_id.id == budget_analytic_id)
                if budget_line:
                    if self.type == 'report' and float_compare(budget_amount, budget_line.planning_budget_amount, 2) !=0:
                        budget_line.write(
                            {'planning_budget_amount': budget_amount})
                    elif self.type == 'budget' and float_compare(budget_amount, budget_line.budget_amount, 2) !=0:
                        budget_line.write(
                            {'budget_amount': budget_amount})
            oos_mappings = self.env['oos.mapping'].sudo().search([('company_id', '=', self.company_id.id)])
            oos_mappings._compute_budget_account_id()
