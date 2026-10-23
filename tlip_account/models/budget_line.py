from odoo import fields, models
from odoo.tools import SQL


class BudgetLine(models.Model):
    _inherit = "budget.line"

    planning_budget_amount = fields.Monetary(string="Report")
    committed_amount = fields.Monetary(string="Reserved")
    achieved_amount = fields.Monetary(string="Used")
    budget_line_detail_ids = fields.One2many(
        'budget.line.detail', 'budget_line_id', string='Budget Analytic Details'
    )
    budget_department_id = fields.Many2one(
        "budget.department",
        string="Department",
        store=True,
        related="account_id.budget_department_id"
    )
    complete_code = fields.Char(
        string="Full Code",
        store=True,
        related="account_id.complete_code"
    )
    budget_main_categ_id = fields.Many2one(
        'budget.category',
        related='account_id.budget_main_categ_id', store=True,
        string='Budget Main Category'
    )
    budget_2nd_categ_id = fields.Many2one(
        'budget.category',
        related='account_id.budget_2nd_categ_id', store=True,
        string='Budget Secondary Category'
    )
    budget_detailed_categ_id = fields.Many2one(
        'budget.category',
        related='account_id.budget_category_id', store=True,
        string='Budget Detailed Category'
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
        self.mapped("account_id")
        self.mapped("budget_analytic_id")
        self.mapped("budget_amount")

        dest_budget_line_grouped = self._get_amount_by_dest_budget_code()
        src_budget_line_grouped = self._get_amount_by_src_budget_code()
        for rec in self:
            account_id = rec.account_id
            budget_analytic = rec.budget_analytic_id
            budget_year = budget_analytic.budget_year_id

            add_amount = dest_budget_line_grouped.get((account_id.id, budget_analytic.id), 0)
            subtract_amount = src_budget_line_grouped.get((account_id.id, rec.date_from, budget_year.id), 0)    # Follow the logic each budget line's date_from is start of month
            additional_amount = add_amount - subtract_amount

            rec.additional_amount = additional_amount
            rec.remained_amount = rec.budget_amount + additional_amount + rec.achieved_amount + rec.committed_amount

    def open_budget_line_details(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'account_budget.act_budget_lines_view')
        action.update({
            'views': [(self.env.ref('tlip_account.view_budget_line_form_detail_line').id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'name': 'Budget Code Details'
        })
        return action

    def _get_amount_by_src_budget_code(self):
        account_ids=f"({', '.join(map(str, self.account_id.ids))})"

        sql_query = SQL(
            f"""
                SELECT 
                    approval.src_budget_code_id,
                    date_trunc('month', approval.issue_date)::date,
                    approval.confirmed_budget_year_id,
                    sum(approval.transfer_amount)
                FROM budget_allocation_approval approval
                WHERE
                    approval.state = 'approved'
                    AND approval.budget_approval_type = 'transfer'
                    AND approval.src_budget_code_id IN {account_ids}
                GROUP BY approval.src_budget_code_id, date_trunc('month', approval.issue_date), approval.confirmed_budget_year_id;
            """
        )
        self.env.cr.execute(sql_query)

        return {
            (result[0], result[1], result[2]): result[3]
            for result in self.env.cr.fetchall()
        }

    def _get_amount_by_dest_budget_code(self):
        account_ids = f"({', '.join(map(str, self.account_id.ids))})"
        budget_analytic_ids = f"({', '.join(map(str, self.budget_analytic_id.ids))})"

        sql_query = SQL(
            f"""
                SELECT 
                    approval.dest_budget_code_id,
                    allocation_line.budget_analytic_id,
                    sum(allocation_line.transfer_amount)
                FROM budget_allocation_approval approval
                JOIN 
                    budget_allocation_line allocation_line ON allocation_line.allocation_id = approval.id
                WHERE
                    approval.state = 'approved'
                    AND approval.dest_budget_code_id IN {account_ids}
                    AND allocation_line.budget_analytic_id IN {budget_analytic_ids}
                GROUP BY approval.dest_budget_code_id, allocation_line.budget_analytic_id;
            """
        )
        self.env.cr.execute(sql_query)

        return {
            (result[0], result[1]): result[2]
            for result in self.env.cr.fetchall()
        }
