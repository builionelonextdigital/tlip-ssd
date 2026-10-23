from odoo import models, fields, api
from odoo.tools import SQL


class BudgetReport(models.Model):
    _inherit = 'budget.report'

    budget_department_id = fields.Many2one(
        "budget.department",
        string="Department"
    )
    complete_code = fields.Char(
        string="Full Code"
    )
    budget_main_categ_id = fields.Many2one(
        'budget.category',
        string='Budget Main Category'
    )
    budget_main_categ_code = fields.Char(
        related='budget_main_categ_id.code',
        string='Budget Main Category Code'
    )
    budget_2nd_categ_id = fields.Many2one(
        'budget.category',
        string='Budget Secondary Category'
    )
    budget_2nd_categ_code = fields.Char(
        related='budget_2nd_categ_id.code',
        string='Budget Main Category Code'
    )
    budget_detailed_categ_id = fields.Many2one(
        'budget.category',
        string='Budget Detailed Category'
    )
    budget_detailed_categ_code = fields.Char(
        related='budget_detailed_categ_id.code',
        string='Budget Main Category Code'
    )

    def _get_bl_query(self, plan_fnames):
        return SQL(
            """
            SELECT CONCAT('bl', bl.id::TEXT) AS id,
                   bl.budget_analytic_id AS budget_analytic_id,
                   bl.id AS budget_line_id,
                   bl.budget_department_id as budget_department_id,
                   bl.complete_code as complete_code,
                   bl.budget_main_categ_id as budget_main_categ_id,
                   bl.budget_2nd_categ_id as budget_2nd_categ_id,
                   bl.budget_detailed_categ_id as budget_detailed_categ_id,
                   'budget.analytic' AS res_model,
                   bl.budget_analytic_id AS res_id,
                   bl.date_from AS date,
                   ba.name AS description,
                   bl.company_id AS company_id,
                   NULL AS user_id,
                   'budget' AS line_type,
                   bl.planning_budget_amount AS budget,
                   0 AS committed,
                   0 AS achieved,
                   %(plan_fields)s
              FROM budget_line bl
              JOIN budget_analytic ba ON ba.id = bl.budget_analytic_id
            """,
            plan_fields=SQL(', ').join(self.env['budget.line']._field_to_sql(
                'bl', fname) for fname in plan_fnames)
        )

    def _get_aal_query(self, plan_fnames):
        return SQL(
            """
            SELECT CONCAT('aal', aal.id::TEXT) AS id,
                   bl.budget_analytic_id AS budget_analytic_id,
                   bl.id AS budget_line_id,
                   bl.budget_department_id as budget_department_id,
                   bl.complete_code as complete_code,
                   bl.budget_main_categ_id as budget_main_categ_id,
                   bl.budget_2nd_categ_id as budget_2nd_categ_id,
                   bl.budget_detailed_categ_id as budget_detailed_categ_id,
                   'account.analytic.line' AS res_model,
                   aal.id AS res_id,
                   aal.date AS date,
                   aal.name AS description,
                   aal.company_id AS company_id,
                   aal.user_id AS user_id,
                   'achieved' AS line_type,
                   0 AS budget,
                   0 AS committed,
                   aal.amount * CASE WHEN ba.budget_type = 'expense' THEN -1 ELSE 1 END AS achieved,
                   %(analytic_fields)s
              FROM account_analytic_line aal
         LEFT JOIN budget_line bl ON aal.company_id = bl.company_id
                                 AND aal.date >= bl.date_from
                                 AND aal.date <= bl.date_to
                                 AND %(condition)s
         LEFT JOIN account_account aa ON aa.id = aal.general_account_id
         LEFT JOIN budget_analytic ba ON ba.id = bl.budget_analytic_id
            """,
            analytic_fields=SQL(', ').join(self.env['account.analytic.line']._field_to_sql(
                'aal', fname) for fname in plan_fnames),
            condition=SQL(' AND ').join(SQL(
                "(%(bl)s IS NULL OR %(aal)s = %(bl)s)",
                bl=self.env['budget.line']._field_to_sql('bl', fname),
                aal=self.env['budget.line']._field_to_sql('aal', fname),
            ) for fname in plan_fnames)
        )

    def _get_pol_query(self, plan_fnames):
        return SQL(
            """
            SELECT (br.id::TEXT || '-' || ROW_NUMBER() OVER (PARTITION BY br.id ORDER BY br.id)) AS id,
                   bl.budget_analytic_id AS budget_analytic_id,
                   bl.id AS budget_line_id,
                   bl.budget_department_id as budget_department_id,
                   bl.complete_code as complete_code,
                   bl.budget_main_categ_id as budget_main_categ_id,
                   bl.budget_2nd_categ_id as budget_2nd_categ_id,
                   bl.budget_detailed_categ_id as budget_detailed_categ_id,
                   'request.purchase' AS res_model,
                   br.id AS res_id,
                   br.date AS date,
                   br.name AS description,
                   br.company_id AS company_id,
                   br.user_id AS user_id,
                   'committed' AS line_type,
                   0 AS budget,
                   br.amount * -1 AS committed,
                   0 AS achieved,
                   br.account_id
              FROM budget_reserved br
         LEFT JOIN budget_line bl ON br.company_id = bl.company_id
                                 AND br.date >= bl.date_from
                                 AND br.date <= bl.date_to
                                 AND %(condition)s
         LEFT JOIN budget_analytic ba ON ba.id = bl.budget_analytic_id
             WHERE ba.budget_type != 'revenue'
                AND br.amount > 0
            """,
            condition=SQL(' AND ').join(SQL(
                "(%(bl)s IS NULL OR %(a)s = %(bl)s)",
                bl=self.env['budget.line']._field_to_sql('bl', fname),
                a=self.env['budget.line']._field_to_sql('br', fname),
            ) for fname in plan_fnames)
        )

    @api.model
    def _get_domain_budget_report(self, analytic_report_xml=False):
        opening_budget_years = self.env['budget.analytic.year'].search(
            [('state', '=', 'confirmed')])
        budget_analytic_ids = opening_budget_years.mapped(
            'monthly_line_ids').ids
        filter_domain = [('budget_analytic_id', 'in', budget_analytic_ids),
                         ('complete_code', '!=', False)]
        if analytic_report_xml:
            analytic_report = self.env.ref(analytic_report_xml)
            if analytic_report:
                filter_domain.append(
                    ('account_id', 'in', analytic_report.line_ids.mapped('account_id').ids))
        return filter_domain

    def _open_budget_report_based_analytic_report(self, filter_by_report=False, display_name="Budget Report"):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_account.action_analytic_report_window')
        filter_domain = self._get_domain_budget_report(filter_by_report)
        action.update({
            'display_name': display_name,
            'domain': filter_domain,
            'context': {
                'download_analytic_report': True,
                'analytic_report_xml': filter_by_report,
                'analytic_report_name': display_name
            }
        })
        return action

    @api.model
    def action_open_sales_report(self):
        filter_by_report = 'tlip_account.analytic_report_sales'
        display_name = 'Sales Report'
        return self._open_budget_report_based_analytic_report(filter_by_report, display_name)

    @api.model
    def action_open_investment_plan_projection(self):
        filter_by_report = 'tlip_account.analytic_report_investment_plan'
        display_name = 'Investment Plan Projection'
        return self._open_budget_report_based_analytic_report(filter_by_report, display_name)

    @api.model
    def action_open_operation_misc(self):
        filter_by_report = 'tlip_account.analytic_report_operation_misc'
        display_name = 'Operation & Miscellaneous Expenses'
        return self._open_budget_report_based_analytic_report(filter_by_report, display_name)

    @api.model
    def action_open_direct_cost_report(self):
        filter_by_report = 'tlip_account.analytic_report_direct_cost'
        display_name = 'Direct Cost Report'
        return self._open_budget_report_based_analytic_report(filter_by_report, display_name)

    @api.model
    def download_budget_analytic_report(self, report_name):
        return True
