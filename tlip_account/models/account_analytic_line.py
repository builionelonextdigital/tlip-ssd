from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

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
    oos_mapping_id = fields.Many2one(
        'oos.mapping', related='move_line_id.oos_mapping_id',
        store=True)

    # The code below is commented out as the oos_mapping_id now retrieved from the HRMS synced move line.
    # In case client wants to handle manual journal entries with oos_mapping_id, we can consider re-enabling

    # @api.depends('account_id.budget_code_id', 'company_id', 'move_line_id.ctp_account_ids', 'move_line_id.cr_ctp_ids', 'move_line_id.dr_ctp_ids')
    # def _compute_oos_mapping_id(self):
    #     existing_oos_mappings = self.env["oos.mapping"].search([])
    #     oos_accounts = existing_oos_mappings.mapped("credit_account_id") \
    #         + existing_oos_mappings.mapped("debit_account_id")

    #     for line in self:
    #         oos_mapping = False
    #         account = line.general_account_id
    #         aml = line.move_line_id

    #         if account in oos_accounts and line.account_id.budget_code_id and abs(line.amount) > 0 and (aml.cr_ctp_ids or aml.dr_ctp_ids):
    #             if aml.cr_ctp_ids:
    #                 debit_accounts = [aml.account_id.id]
    #                 credit_accounts = aml.mapped('ctp_account_ids').ids[:1]
    #             if aml.dr_ctp_ids:
    #                 credit_accounts = [aml.account_id.id]
    #                 debit_accounts = aml.mapped('ctp_account_ids').ids[:1]

    #             domain = [
    #                 ("budget_code_id", "=", line.account_id.budget_code_id.id),
    #                 ("credit_account_id", "in", credit_accounts),
    #                 ("debit_account_id", "in", debit_accounts),
    #                 ("company_id", "=", line.company_id.id),
    #             ]
    #             oos_mapping = existing_oos_mappings.filtered_domain(domain)[:1]

    #         line.oos_mapping_id = oos_mapping
