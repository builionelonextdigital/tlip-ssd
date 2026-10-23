from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OOSMapping(models.Model):
    _name = 'oos.mapping'
    _description = 'OOS Mapping'
    _rec_name = 'item_code'

    item_code = fields.Char('Item Code', required=True)
    item_name = fields.Char('Item Name', required=True)
    budget_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        compute='_compute_budget_account_id',
        store=True,
        string='Budget Account Code'
    )
    budget_code_id = fields.Many2one('budget.code', string='Budget Code')
    budget_complete_code = fields.Char(
        related='budget_account_id.complete_code', store=True)
    debit_account_id = fields.Many2one('account.account', required=True)
    credit_account_id = fields.Many2one('account.account', required=True)
    company_id = fields.Many2one('res.company', required=True)
    description = fields.Char(required=True)
    partner_debit_id = fields.Many2one('res.partner')
    partner_credit_id = fields.Many2one('res.partner')
    category_id = fields.Many2one('oos.mapping.category')

    @api.constrains('item_code', 'budget_code_id', 'company_id')
    def _contrains_unique_oos_mapping(self):
        for record in self:
            duplicate_oos_counts = record.search_count(
                [("company_id", "=", record.company_id.id),
                 ("item_code", "=", record.item_code),
                 ("budget_code_id", "=", record.budget_code_id.id),
                 ("id", "!=", record.id)]
            )
            if duplicate_oos_counts > 0:
                raise UserError(
                    _(f"{record.item_name} - {record.budget_code_id.code} of company {record.company_id.name} had existed. Please check again."))

    @api.depends('budget_code_id', 'company_id')
    def _compute_budget_account_id(self):
        analytic_accounts = self.env['account.analytic.account'].search([])
        for record in self:
            record.budget_account_id = analytic_accounts.filtered(
                lambda r: r.company_id.id == record.company_id.id and r.budget_code_id.id == record.budget_code_id.id)[:1]
