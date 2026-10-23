from odoo import models, fields, api
from odoo.tools import SQL


class SalaryDistributionReport(models.Model):
    _name = "salary.distribution.report"
    _description = "Salary Distribution Report"
    _auto = False
    _rec_name = 'oos_description'
    _order = 'oos_description'

    amount = fields.Monetary(string='Amount', readonly=True)
    item_code = fields.Char('Item Code', readonly=True)
    item_name = fields.Char('Item Name', readonly=True)
    budget_code_id = fields.Many2one(
        'budget.code', string='Budget Code', readonly=True)
    oos_description = fields.Char('OOS Description', readonly=True)
    category_id = fields.Many2one('oos.mapping.category', 'Category',
                                  readonly=True)
    parent_category_id = fields.Many2one('oos.mapping.category', 'Category',
                                         readonly=True)
    credit_account_id = fields.Many2one('account.account', string='Credit Account',
                                        readonly=True)
    debit_account_id = fields.Many2one('account.account', string='Debit Account',
                                        readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', readonly=True)

    _depends = {
        'account.analytic.line': [
            'amount', 'company_id', 'currency_id'
        ],
        'oos.mapping': ['category_id', 'item_code', 'item_name', 'budget_code_id', 'description', 'credit_account_id', 'debit_account_id'],
        'oos.mapping.category': ['parent_id'],
    }

    @property
    def _table_query(self) -> SQL:
        return SQL('%s %s %s', self._select(), self._from(), self._where())

    @api.model
    def _select(self) -> SQL:
        return SQL(
            '''
            SELECT
                row_number() over() as id,
                oos.category_id,
                oos_category.parent_id AS parent_category_id,
                oos.item_code,
                oos.item_name,
                oos.budget_code_id,
                oos.description AS oos_description,
                ABS(SUM(aal.amount)) as amount,
                oos.credit_account_id,
                oos.debit_account_id,
                aal.currency_id,
                oos.company_id
            ''',
        )

    @api.model
    def _from(self) -> SQL:
        return SQL(
            '''
            FROM oos_mapping oos
                LEFT JOIN account_analytic_line aal ON aal.oos_mapping_id = oos.id
                LEFT JOIN oos_mapping_category oos_category ON oos_category.id = oos.category_id
            ''',
        )

    @api.model
    def _where(self) -> SQL:
        return SQL(
            '''
            GROUP BY oos.category_id,
                oos_category.parent_id,
                oos.item_code,
                oos.item_name,
                oos.budget_code_id,
                oos.description,
                oos.credit_account_id,
                oos.debit_account_id,
                aal.currency_id,
                oos.company_id
            ''',
        )
