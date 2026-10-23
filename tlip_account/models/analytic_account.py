from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountAnalyticAccount(models.Model):
    _name = "account.analytic.account"
    _inherit = ['account.analytic.account', 'approval.matrix.mixin']
    _rec_names_search = ['name', 'code']

    def _get_default_analytic_plan(self):
        return self.env["account.analytic.plan"].search([], limit=1)

    name = fields.Char(string="Analytic Account", compute='_compute_code', store=True)
    code = fields.Char(
        string="Code",
        copy=False,
        required=True,
        compute='_compute_code',
        store=True
    )
    budget_code_id = fields.Many2one('budget.code', string='Budget Code', copy=True, required=True, index=True)
    budget_department_id = fields.Many2one('budget.department', string='Department')

    budget_category_id = fields.Many2one(
        "budget.category",
        string="Category",
        required=True,
        copy=True,
        compute='_compute_budget_category_id', store=True
    )

    default_account_id = fields.Many2one('account.account', string="Default Account", compute='_compute_default_account_id')
    default_account_ids = fields.Many2many('account.account', string='Default Accounts', copy=True)
    plan_id = fields.Many2one(default=_get_default_analytic_plan, copy=True)
    budget_main_categ_id = fields.Many2one(
        'budget.category',
        compute='_compute_category_id', store=True,
        string='Budget Main Category'
    )
    budget_2nd_categ_id = fields.Many2one(
        'budget.category',
        compute='_compute_category_id', store=True,
        string='Budget Secondary Category'
    )
    complete_code = fields.Char(
        'Complete Code', compute='_compute_complete_code',
        store=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait_for_approval", "Waiting for Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ('cancel', 'Cancelled')
    ], string="Status", default="draft", tracking=True, copy=True)
    
    budget_amount = fields.Monetary(
        compute="_compute_amount",
        string="Budget"
    )
    committed_amount = fields.Monetary(
        string="Reserved",
        compute="_compute_amount",
    )
    achieved_amount = fields.Monetary(
        string="Used",
        compute="_compute_amount",
    )
    remained_amount = fields.Monetary(
        string="Remained",
        compute="_compute_amount",
    )
    additional_amount = fields.Monetary(
        string="Additional",
        compute="_compute_amount",
    )

    def _compute_amount(self):
        current_planning = self.env['budget.analytic.year'].search([('state', '=', 'confirmed')], limit=1)
        budget_line_grouped = current_planning.budget_line_year_ids._get_amount_by_grouped_budget()
        for rec in self:
            _ , budget, committed, achieved, additional = budget_line_grouped.get(
                rec,
                (0, 0, 0, 0, 0),
            )
            rec.budget_amount = budget
            rec.committed_amount = committed
            rec.achieved_amount = achieved
            rec.additional_amount = additional
            rec.remained_amount = budget + additional + achieved + committed
    
    @api.depends('default_account_ids')
    @api.depends_context('company')
    def _compute_default_account_id(self):
        company = self.env["res.company"].browse(self._context.get("company_id")) if self._context.get("company_id") else self.env.company
        for record in self:
            record.default_account_id = record.default_account_ids.filtered(lambda r: company.id in r.company_ids.ids)[:1]

    @api.depends('budget_code_id', 'budget_department_id')
    def _compute_code(self):
        for record in self:
            record.code = f"{record.budget_department_id.code}-{record.budget_code_id.code}"
            record.name = record.budget_code_id.name

    @api.depends('budget_code_id')
    def _compute_budget_category_id(self):
        for record in self:
            record.budget_category_id = record.budget_code_id.budget_category_id

    @api.depends('budget_category_id')
    def _compute_category_id(self):
        for rec in self:
            budget_main_categ_id = False
            parent_categ_id = rec.budget_category_id.parent_id
            # Check 3rd level category
            if parent_categ_id.parent_id:
                budget_main_categ_id = parent_categ_id.parent_id
            rec.budget_main_categ_id = budget_main_categ_id
            rec.budget_2nd_categ_id = parent_categ_id

    @api.depends('budget_code_id.code', 'budget_department_id')
    def _compute_complete_code(self):
        for budget in self:
            budget.complete_code = f'{budget.budget_department_id.code}-{budget.budget_code_id.code}'

    @api.constrains("code", "company_id", "budget_department_id")
    def _constrains_code(self):
        for record in self:
            if not record.code:
                continue
            duplicate_code_counts = self.search(
                [("company_id", "=", record.company_id.id),
                 ("code", "=", record.code),
                 ("budget_department_id", "=", record.budget_department_id.id),
                 ("budget_category_id", "=", record.budget_category_id.id),
                 ("id", "!=", record.id)]
            )
            if len(duplicate_code_counts) > 0:
                raise UserError(
                    _(f"Code '{record.code}' had existed. Please check again."))
    
    @api.model            
    def _get_analytic_account_id(self, budget_code, company_id):
        analytic_account = self.env['account.analytic.account'].search([('budget_code_id', '=', budget_code.id),
                                                                        ('company_id', '=', company_id)], limit=1)
        return analytic_account

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action['context']['default_name'] = _(
            f'Approval Budget Code {self.name}')
        return action

    def action_reset(self):
        self.write({
            "state": 'draft',
            "approval_request_id": False,
        })

    def action_cancel(self):
        self.write({"state": "cancel"})

    def _trigger_action_approve(self):
        self.write({'state': 'approved'})
        if 'bypass_approval' not in self.env.context:
            budget_years = self.env["budget.analytic.year"].search(
                [("state", "=", "confirmed")])
            if budget_years:
                budget_years.action_add_new_budget_code(analytic_accounts=self)

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval',
        })
        return result

    def _trigger_action_withdraw(self, reason: str):
        self.action_cancel()
        super()._trigger_action_withdraw(reason)

    def _validate_submit_approval(self):
        if self.filtered(lambda r: r.state != 'draft'):
            raise UserError(
                _('You cannot submit a budget code that is not in Draft state.'))

    @api.model_create_multi
    def create(self, vals_list):
        default_plan = self._get_default_analytic_plan()
        for vals in vals_list:
            if not vals.get('plan_id'):
                vals['plan_id'] = default_plan.id
        res = super().create(vals_list)
        if 'bypass_approval' in self.env.context:
            res._trigger_action_approve()
        return res
