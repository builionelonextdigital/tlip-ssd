from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class BudgetAllocationApproval(models.Model):
    _name = "budget.allocation.approval"
    _description = "Budget Approval"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'approval.matrix.mixin']
    _order = 'priority desc, id asc'

    def _default_open_budget_analytic_year(self):
        budget_analytic_year = self.env["budget.analytic.year"].get_current_budget_analytic_year()
        if not budget_analytic_year:
            raise UserError(_("Please enable the Budget Yearly"))

        return budget_analytic_year.id

    confirmed_budget_year_id = fields.Many2one("budget.analytic.year", default=_default_open_budget_analytic_year)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ('cancel', 'Cancelled')
        ], string="Status", default="draft", tracking=True
    )
    name = fields.Char(
        string="Budget Approval", required=True, default="New",
        copy=False, index='trigram', tracking=True
    )
    priority = fields.Selection(selection=[
        ('0', 'Normal'), ('1', 'Urgent')],
        string='Priority', default='0', required=True
    )
    budget_approval_type = fields.Selection(
        selection=[
            ('additional', 'Additional Budget'),
            ('transfer', 'Transfer Budget'),
        ], string='Budget Approval Type', 
        default='additional', required=True, tracking=True
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Requester",
        check_company=True, tracking=True, required=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company.id,
        required=True, index=True,
        ondelete="cascade"
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id'
    )
    date_from = fields.Date('Date From', required=True, tracking=True)
    date_to = fields.Date('Date To', required=True, tracking=True)
    budget_category_id = fields.Many2one(
        comodel_name='budget.category',
        string='Budget Category',
        tracking=True, required=True
    )
    ref = fields.Char(string='Reference')
    issue_date = fields.Datetime(
        string="Issue Date",
        tracking=True, required=True,
        default=fields.Datetime.now
    )
    period_str = fields.Char(compute="_compute_period_str", string="Period")
    budget_allocation_line_ids = fields.One2many(
        comodel_name="budget.allocation.line",
        inverse_name="allocation_id",
        string="Budget Allocation", required=True
    )
    transfer_amount = fields.Monetary(
        compute="_compute_transfer_amount",
        store=True,
    )
    # Destination Budget Code
    dest_budget_code_id = fields.Many2one(
        comodel_name="account.analytic.account",
        domain="[('budget_category_id', '=', budget_category_id), ('state', '=', 'approved'), ('company_id', '=', company_id)]",
        check_company=True,
        string="Destination Budget Code", required=True
    )
    dest_budget_amount = fields.Monetary(
        string="Destination Budgeted",
        compute="_compute_budget_amount"
    )
    dest_committed_amount = fields.Monetary(
        string="Destination Reserved",
        compute="_compute_budget_amount")
    dest_achieved_amount = fields.Monetary(
        string="Destination Used",
        compute="_compute_budget_amount"
    )
    dest_prev_additional_amount = fields.Monetary(
        string="Destination Previous Additional",
        compute="_compute_dest_budget_amount",
        store=True
    )
    dest_origin_remained_amount = fields.Monetary(
        string="Destination Origin Remained",
        compute="_compute_dest_budget_amount",
        store=True
    )
    dest_new_remained_amount = fields.Monetary(
        string="Destination New Remained",
        compute="_compute_dest_budget_amount",
        store=True
    )

    # Source Budget Code
    src_budget_code_id = fields.Many2one(
        comodel_name="account.analytic.account",
        domain="[('budget_category_id', '=', budget_category_id), ('state', '=', 'approved'), ('company_id', '=', company_id)]",
        check_company=True,
        string="Source Budget Code"
    )
    src_budget_amount = fields.Monetary(
        string="Source Budgeted",
        compute="_compute_budget_amount"
    )
    src_committed_amount = fields.Monetary(
        string="Source Reserved",
        compute="_compute_budget_amount")
    src_achieved_amount = fields.Monetary(
        string="Source Used",
        compute="_compute_budget_amount"
    )
    src_prev_additional_amount = fields.Monetary(
        string="Source Previous Additional",
        compute="_compute_src_budget_amount",
        store=True
    )
    src_origin_remained_amount = fields.Monetary(
        string="Source Origin Remained",
        compute="_compute_src_budget_amount",
        store=True
    )
    src_new_remained_amount = fields.Monetary(
        string="Source New Remained",
        compute="_compute_src_budget_amount",
        store=True
    )
    src_transfer_amount = fields.Monetary(string="Source Additional Amount", compute="_compute_src_transfer_amount")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if any(record.date_from > record.date_to for record in self):
            raise ValidationError(_("Start date should precede the end date."))

    @api.depends("budget_allocation_line_ids.transfer_amount")
    def _compute_transfer_amount(self):
        self.mapped("budget_allocation_line_ids")
        for rec in self:
            rec.transfer_amount = sum(rec.budget_allocation_line_ids.mapped("transfer_amount"))

    @api.depends("confirmed_budget_year_id", "dest_budget_code_id", "src_budget_code_id")
    def _compute_budget_amount(self):
        line_grouped_account = self.confirmed_budget_year_id.budget_line_year_ids.get_amount_by_grouped_account(budget_fields=["budget_amount", "committed_amount", "achieved_amount"])
        for rec in self:
            dest_account_dict = line_grouped_account.get(rec.dest_budget_code_id, defaultdict(int))
            src_account_dict = line_grouped_account.get(rec.src_budget_code_id, defaultdict(int))

            rec.dest_budget_amount = dest_account_dict["budget_amount"]
            rec.dest_committed_amount = dest_account_dict["committed_amount"]
            rec.dest_achieved_amount = dest_account_dict["achieved_amount"]
            rec.src_budget_amount = src_account_dict["budget_amount"]
            rec.src_committed_amount = src_account_dict["committed_amount"]
            rec.src_achieved_amount = src_account_dict["achieved_amount"]

    @api.depends("confirmed_budget_year_id", "dest_budget_code_id", "transfer_amount")
    def _compute_dest_budget_amount(self):
        line_grouped_account = self.confirmed_budget_year_id.budget_line_year_ids.get_amount_by_grouped_account(budget_fields=["additional_amount", "remained_amount"])
        for rec in self:
            dest_account_dict = line_grouped_account.get(rec.dest_budget_code_id, defaultdict(int))

            dest_prev_additional_amount = dest_account_dict["additional_amount"]
            dest_origin_remained_amount = dest_account_dict["remained_amount"]

            rec.dest_prev_additional_amount = dest_prev_additional_amount
            rec.dest_origin_remained_amount = dest_origin_remained_amount
            rec.dest_new_remained_amount = dest_origin_remained_amount + rec.transfer_amount

    @api.depends("confirmed_budget_year_id", "src_budget_code_id", "transfer_amount")
    def _compute_src_budget_amount(self):
        line_grouped_account = self.confirmed_budget_year_id.budget_line_year_ids.get_amount_by_grouped_account(budget_fields=["additional_amount", "remained_amount"])
        for rec in self:
            src_account_dict = line_grouped_account.get(rec.src_budget_code_id, defaultdict(int))

            src_prev_additional_amount = src_account_dict["additional_amount"]
            src_origin_remained_amount = src_account_dict["remained_amount"]

            rec.src_prev_additional_amount = src_prev_additional_amount
            rec.src_origin_remained_amount = src_origin_remained_amount
            rec.src_new_remained_amount = src_origin_remained_amount - rec.transfer_amount

    def _compute_period_str(self):
        date_format = self.env['res.lang']._lang_get(self.env.user.lang).date_format
        for record in self:
            start = record.date_from \
                and record.date_from.strftime(date_format) or ''
            end = record.date_to \
                and record.date_to.strftime(date_format) or ''
            record.period_str = f'{start} - {end}'

    @api.onchange("budget_category_id")
    def _onchange_budget_category_id(self):
        self.ensure_one()
        if self.budget_category_id != self.dest_budget_code_id.budget_category_id:
            self.dest_budget_code_id = False
            self.src_budget_code_id = False

    @api.onchange("budget_approval_type")
    def _onchange_budget_approval_type(self):
        self.ensure_one()
        if self.budget_approval_type == "additional" and self.src_budget_code_id:
            self.src_budget_code_id = False

    @api.depends("transfer_amount")
    def _compute_src_transfer_amount(self):
        for rec in self:
            rec.src_transfer_amount = -rec.transfer_amount

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action['context']['default_name'] = _(f'Budget Approval {self.name}')
        return action

    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })

    def action_reset(self):
        self.write({
            'state': 'draft',
        })

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval',
        })
        return result

    def _validate_submit_approval(self):
        for record in self:
            if not record.budget_allocation_line_ids:
                raise UserError(_("Budget Allocation is missing. Please fill in and continue."))

            if len(record.budget_allocation_line_ids) != len(record.budget_allocation_line_ids.budget_analytic_id):
                raise UserError(_("Monthly Budget should not be duplicate."))

            # Check overlap with period
            date_from = record.date_from
            date_to = record.date_to
            invalid_lines = record.budget_allocation_line_ids.filtered(
                lambda line, date_from=date_from, date_to=date_to: \
                    date_from > line.budget_analytic_id.date_from or date_to < line.budget_analytic_id.date_to
            )

            if invalid_lines:
                raise ValidationError(
                    _(f"Allocation(s) {', '.join(invalid_lines.budget_analytic_id.mapped('name'))} "\
                      f"overlap with the period {record.period_str}"))

            # Check negative budget allocation
            negative_lines = record.budget_allocation_line_ids.filtered(lambda line: line.transfer_amount <= 0)
            if negative_lines:
                raise ValidationError(
                    _(f"Allocation(s) {', '.join(negative_lines.budget_analytic_id.mapped('name'))} "\
                       "should have transfer amount larger than 0"))

            if record.budget_approval_type == "transfer":
                if record.src_budget_code_id == record.dest_budget_code_id:
                    raise UserError(_("Source Budget Code should not be the same with Destination Budget Code"))

                if float_compare(
                    record.transfer_amount, record.src_budget_code_id.remained_amount, precision_rounding=record.currency_id.rounding
                ) > 0:
                    raise UserError(_(f"Cannot transfer amount larger than remained amount of Source Budget Code ({self.src_budget_code_id.remained_amount})"))

    def _trigger_action_approve(self):
        self.write({'state': 'approved'})

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get("date_from") and vals.get("date_to") and vals["date_from"] > vals["date_to"]:
                raise ValidationError(_("Start date should precede the end date."))

            vals['name'] = IrSequence.next_by_code('budget.allocation.approval')
        return super(BudgetAllocationApproval, self).create(vals_list)
