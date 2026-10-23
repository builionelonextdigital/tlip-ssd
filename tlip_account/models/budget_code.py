from odoo import api, fields, models, _
from odoo.osv import expression

class BudgetCode(models.Model):
    _name = 'budget.code'
    _description = 'Budget Code'
    _rec_name = 'code'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    budget_category_id = fields.Many2one(
        "budget.category",
        string="Category",
        required=True,
        copy=True
    )
    default_account_id = fields.Many2one('account.account', string="Default Account", compute='_compute_default_account_id')
    default_account_ids = fields.Many2many('account.account', string='Default Accounts', copy=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Budge Code must be unique !')
    ]
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        codes = self.search_fetch(domain, ['name'], limit=limit)
        return [(code.id, code.name) for code in codes.sudo()]

    @api.depends('default_account_ids')
    @api.depends_context('company')
    def _compute_default_account_id(self):
        company = self.env["res.company"].browse(self._context.get("company_id")) if self._context.get("company_id") else self.env.company
        for record in self:
            record.default_account_id = record.default_account_ids.filtered(lambda r: company.id in r.company_ids.ids)[:1]

    def _get_analytic_account(self, company_id):
        self.ensure_one()
        return self.env['account.analytic.account'].search([('budget_code_id', '=', self.id),
                                                            ('company_id', '=', company_id)], limit=1)
