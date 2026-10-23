from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BudgetCategory(models.Model):
    _name = 'budget.category'
    _description = '''Budget Category'''
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _rec_names_search = ['code', 'name']
    _order = 'complete_name'

    name = fields.Char(string="Budget Category", required=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name', recursive=True,
        store=True)
    code = fields.Char(
        string="Code",
        copy=False,
        required=True
    )
    parent_id = fields.Many2one(
        "budget.category",
        string="Parent Category",
        ondelete='cascade'
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        "budget.category",
        "parent_id",
        copy=False
    )
    budget_code_ids = fields.One2many(
        "account.analytic.account", "budget_category_id")
    count_budget_code = fields.Integer(compute="_compute_count_budget_code")

    @api.constrains("code")
    def _constrains_code(self):
        for record in self:
            if not record.code:
                continue
            duplicate_code_counts = record.search_count(
                [("code", "=", record.code),
                 ("parent_id", "=", record.parent_id.id),
                 ("id", "!=", record.id)]
            )
            if duplicate_code_counts > 0:
                raise UserError(
                    _(f"Code '{record.code}' had existed. Please check again."))

    @api.constrains('parent_id')
    def _check_parent_not_circular(self):
        if self._has_cycle():
            raise ValidationError(
                _('Error ! You cannot create recursive categories.'))

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (
                    category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_count_budget_code(self):
        read_group_res = self.env['account.analytic.account']._read_group(
            [('budget_category_id', 'child_of', self.ids)], ['budget_category_id'], ['__count'])
        group_data = {categ.id: count for categ, count in read_group_res}
        for categ in self:
            count_budget_code = 0
            for sub_categ_id in categ.search([('id', 'child_of', categ.ids)]).ids:
                count_budget_code += group_data.get(sub_categ_id, 0)
            categ.count_budget_code = count_budget_code

    def action_view_budget_codes(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'analytic.action_account_analytic_account_form')
        action['domain'] = [('budget_category_id', 'child_of', self.ids)]
        action['context'] = {"default_budget_category_id": self.id}
        return action
