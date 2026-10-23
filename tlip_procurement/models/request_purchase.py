from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools import groupby, float_compare
from odoo.tools.safe_eval import safe_eval


class RequestPurchase(models.Model):
    _name = "request.purchase"
    _description = "Request for Goods/Service"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'approval.matrix.mixin']
    _order = 'priority desc, id desc'

    name = fields.Char(
        string="Request Purchase", required=True, default="New",
        copy=False, index='trigram', tracking=True
    )

    # selection fields
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait_for_approval", "Waiting for Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ('cancel', 'Cancelled')
    ], string="Status", default="draft", tracking=True, copy=False)
    priority = fields.Selection(selection=[
        ('0', 'Normal'), ('1', 'Urgent')],
        string='Priority', default='0'
    )
    select_bidding = fields.Selection(selection=[
        ('bidding', 'Bidding'),
        ('non_bidding', 'Non-Bidding')],
        default='non_bidding',
        string='Bidding/Non-Bidding')
    request_type = fields.Selection(selection=[
        ('normal', 'Normal'),
        ('special', 'Special'),
        ('special_auth', 'Special - Authority'),
    ], string="Request Type", default="normal", required=True, tracking=True
    )
    frequency = fields.Selection(selection=[
        ('infrequent', 'Infrequent'),
        ('over_12mo', '> 12 months'),
        ('recursive', 'Recursive')
    ], string="Procurement Frequency", tracking=True, required=True,)
    category = fields.Selection([
        ('goods_service', 'Goods/Service'),
        ('entertainment', 'Entertainment / Special Requests'),],
        string="Category",
        tracking=True,
    )

    # relational fields
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Applicant",
        default=lambda self: self.env.user,
        check_company=True, tracking=True, required=True,
    )
    budget_department_id = fields.Many2one(
        comodel_name="budget.department",
        string="Department", tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company.id,
        required=True, index=True,
        ondelete="cascade"
    )
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string="Reference Supplier",
        check_company=True,
        domain="[('vendor_state', '=', 'approved'), ('is_blocked', '=', False)]",
    )
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    request_line_ids = fields.One2many(
        comodel_name='request.purchase.line', inverse_name="request_id")
    requirement_line_ids = fields.One2many(
        'request.purchase.requirement.line', 'request_id')

    # date fields
    issue_date = fields.Date(
        string="Issue Date", tracking=True, default=fields.Date.today(), required=True)
    date_order = fields.Date(
        string="Order Deadline", default=fields.Date.today(), required=True)
    date_planned = fields.Date(
        string="Expected Arrival", default=fields.Date.today(), required=True)
    date_expected_activity = fields.Date(
        string="Expected Date of Activity", default=fields.Date.today(), required=True)

    # logics fields
    number_of_participants = fields.Integer(string='Number of Participants', required=True, default=1)
    number_of_months = fields.Integer(string='# Months')
    to_apply_tender = fields.Boolean(string="Apply Tender", tracking=True)
    amount_total = fields.Monetary(
        string="Total Amount", store=True, readonly=True, compute='_amount_all')
    tender_reason = fields.Char(string="Reason")
    purpose = fields.Text(string='Description', required=True)
    exceed_amount_explanation = fields.Text(string='Explanation')
    show_explanation = fields.Boolean(
        string='Show Explanation?',
        compute='_compute_show_explanation',
        store=True
    )
    checklist = fields.Html(
        name='Checklist', compute="_compute_checklist_template", store=True, readonly=False)
    payment_ids = fields.One2many('account.payment', 'request_purchase_id')
    hide_cancel_button = fields.Boolean(compute="_compute_hide_cancel_button")
    move_ids = fields.One2many('account.move', 'request_purchase_id')
    is_advance_required = fields.Boolean(string='Advance Required', default=False)
    advance_amount = fields.Monetary(string='Advance Amount')
    invoice_count = fields.Integer(compute="_compute_invoice", string='Bill Count', copy=False, default=0, store=True)
    invoice_ids = fields.Many2many('account.move', compute="_compute_invoice", string='Bills', copy=False, store=True)
    remaining_invoiced_amount = fields.Float(
        string='Remaining Amount',
        compute='_get_invoiced',
        store=True,
        readonly=True,
        copy=False,
    )
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')
    analytic_line_ids = fields.One2many(
        'account.analytic.line', 'request_purchase_id', string='Analytic Lines')
    is_locked = fields.Boolean(string='Is Locked')

    @api.depends('state', 'invoice_ids', 'category', 'invoice_ids.approval_state', 'amount_total')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for request in self:
            if request.category != 'entertainment' or request.state != 'approved':
                request.remaining_invoiced_amount = 0
                request.invoice_status = 'no'
                continue

            # invoice here has attribute is_request_payment, so always check on approval_state
            amount_untaxed = sum(
                request.invoice_ids.filtered(
                    lambda invoice: invoice.approval_state not in ("draft", "withdrawn")
                    and invoice.state != "cancel"
                ).mapped("amount_untaxed")
            )

            remaining_invoiced_amount = request.amount_total - amount_untaxed
            request.remaining_invoiced_amount = remaining_invoiced_amount
            if float_compare(remaining_invoiced_amount, 0, precision_digits=precision) > 0:
                request.invoice_status = 'to invoice'
            else:
                request.invoice_status = 'invoiced'

    @api.depends('request_line_ids.invoice_lines.move_id')
    def _compute_invoice(self):
        for request in self:
            invoices = request.mapped('request_line_ids.invoice_lines.move_id')
            request.invoice_ids = invoices
            request.invoice_count = len(invoices)

    @api.depends("request_line_ids.price_total")
    def _amount_all(self):
        self.mapped("request_line_ids")
        for rec in self:
            rec.amount_total = sum(rec.request_line_ids.mapped("price_total"))

    @api.depends('number_of_participants', 'amount_total', 'category')
    def _compute_show_explanation(self):
        for request in self:
            show_explanation = False
            if request.category == 'entertainment':
                max_budget_amount = request.company_id.employee_purchase_quota
                if float_compare(
                    request.amount_total/request.number_of_participants,
                    max_budget_amount,
                    precision_digits=request.currency_id.decimal_places
                ) > 0:
                    show_explanation = True

                if not show_explanation:
                    request.exceed_amount_explanation = False

            request.show_explanation = show_explanation

    @api.depends("state", "request_line_ids")
    def _compute_hide_cancel_button(self):
        for rec in self:
            hide_cancel_button = any(task.state != 'canceled' for task in rec.request_line_ids.task_id)
            hide_cancel_button |= (bool(rec.payment_ids) or bool(rec.move_ids))
            rec.hide_cancel_button = hide_cancel_button

    @api.onchange('number_of_participants')
    def _onchange_number_of_participants(self):
        if self.number_of_participants < 1:
            raise UserError(_('The Number of Participants must be positive.'))

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            self.budget_department_id = self.user_id.budget_department_id

    @api.onchange('category')
    def _onchange_category(self):
        if self.category == 'entertainment':
            self.select_bidding = ''
        else:
            self.is_advance_required = False
            self.advance_amount = 0

    @api.onchange('select_bidding')
    def _onchange_select_bidding(self):
        if self.select_bidding == 'bidding':
            self.request_type = 'special'
        else:
            self.request_type = 'normal'

    @api.onchange('budget_department_id')
    def _onchange_budget_department_id(self):
        self.request_line_ids.analytic_account_id = False

    @api.depends('request_type', 'category')
    def _compute_checklist_template(self):
        potential_checklists = self.env['checklist.template'].search([
            ('state', '=', 'confirm'),
            ('related_model_id.model', '=', self[:1]._name)
        ])

        to_update_checklist_requests = self.filtered_domain([
            ('request_type', '=', 'special_auth'),
            ('category', '=', 'entertainment'),
        ])

        for request in to_update_checklist_requests:
            request_checklist = False
            for checklist in potential_checklists:
                checklist_condition = safe_eval(checklist.condition)
                if request.filtered_domain(checklist_condition):
                    request_checklist = checklist.description
                    break

            request.checklist = request_checklist

        (self - to_update_checklist_requests).checklist = False

    def action_submit_approval(self):
        self._validate_submit_approval()
        self._check_budgets()
        action = super().action_submit_approval()
        if action and isinstance(action, dict) and action.get('type') == 'ir.actions.act_window':
            action['context'].update({
                'default_name': _(f'Request for {self.name}'),
                'default_description': self.purpose,
            })
        return action

    def action_reset(self):
        self.write({
            "state": 'draft',
            "approval_request_id": False,
        })

    def action_cancel(self):
        self.write({"state": "cancel"})
        BudgetReservedEnv = self.env['budget.reserved'].sudo()
        BudgetReservedEnv.search([('request_purchase_id', 'in', self.ids)]).unlink()

    def action_view_account_payments(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('account.action_account_payments_payable')
        if len(self.payment_ids) == 1:
            action.update({
                'views': [(self.env.ref('tlip_account.view_payment_request_payment_form').id, 'form')],
                'target': 'current',
                'res_id': self.payment_ids.id,
                'context': {
                    'create': False,
                }
            })
        else:            
            action.update({
                'domain':  [('id', 'in', self.payment_ids.ids)],
                'context': {
                    'default_payment_type': 'outbound',
                    'create': False,
                }
            })
        return action
    
    def action_view_expenses(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_in_invoice_type')
        action.update({
            'context': {'create': False}
        })
        if len(self.move_ids) == 1:
            action.update({
                'views': [(self.env.ref('tlip_procurement.view_request_purchase_expense').id, 'form')],
                'target': 'current',
                'res_id': self.move_ids.id,
            })
        else:
            action.update({
                'views': [
                    (self.env.ref('tlip_account.view_vendor_bill_employee_expense_list_inherit').id, 'list'),
                    (self.env.ref('tlip_procurement.view_request_purchase_expense').id, 'form')
                ],
                'domain': [('id', 'in', self.move_ids.ids)]
            })

        return action

    def action_generate_account_payment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("tlip_procurement.action_procurement_select_request_type")
        action.update({
            'context': {
                'default_request_id': self.id,
                'is_advance_enabled': self.is_advance_required and self.advance_amount > 0,
            }
        })
        return action

    def action_generate_vendor_bill(self):
        account_move_vals = []
        for request in self:
            account_move_vals.append(request._prepare_account_move_vals())
        moves = self.env['account.move'].create(account_move_vals)
        for move in moves:
            subject = _("Vendor Bill %(link)s had been created.", link=move._get_html_link())
            move.request_purchase_id.message_post(body=subject)

    def action_lock_budget(self):
        """Lock the contract and delete draft records (supplements, purchase orders)"""
        self.ensure_one()
        if self.is_locked:
            raise UserError(_("This contract is already locked."))

        if self.state != 'approved' or self.category != 'entertainment':
            raise UserError(_("Only approved entertainment requests can be locked."))

        if not all([
            move.state in ("posted", "cancel") or \
            move.approval_state in ('rejected', 'withdrawn') or \
            move.accounting_approval_state in ('rejected', 'withdrawn') \
            for move in self.move_ids
        ]):
            raise UserError(_("All bills must be posted before locking the request."))
        self.env['budget.reserved'].action_unreserved_amount(requests=self)
        self.write({'is_locked': True})

    def _trigger_action_approve(self):
        self.write({'state': 'approved'})
        entertainment_requests = self.filtered(
            lambda request: request.category == 'entertainment'
        )
        (self - entertainment_requests).filtered(
            lambda request: request.request_type == "special"
        )._create_procurement_tasks_from_request()
        entertainment_requests.action_generate_vendor_bill()

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})
        BudgetReservedEnv = self.env['budget.reserved'].sudo()
        BudgetReservedEnv.search([('request_purchase_id', 'in', self.ids)]).unlink()

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval',
        })
        self._action_create_budget_reserved()
        return result

    def _trigger_action_withdraw(self, reason: str):
        self.action_cancel()
        super()._trigger_action_withdraw(reason)

    def _create_procurement_tasks_from_request(self):
        tasks = self.env["procurement.task"].sudo().create(
            [request._prepare_procurement_task_vals() for request in self])
        for task in tasks:
            activity_message = _(f"Procurement Task {task.name} created and assigned to you.")
            task.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=task.user_id.id,
                note=activity_message,
            )

    def _prepare_procurement_task_vals(self):
        return {
            "user_id": self.user_id.id,
            "company_id": self.company_id.id,
            "date_order": self.date_order,
            "date_planned": self.date_planned,
            "request_line_ids": [(6, 0, self.request_line_ids.ids)],
            "notes": self.name,
            "select_bidding": self.select_bidding,
            "requirement_line_ids": [(6, 0, self.requirement_line_ids.ids)]
        }

    def _validate_submit_approval(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _('You cannot submit a purchase request that is not in Draft state.'))

            if not rec.request_line_ids:
                raise UserError(
                    _('Products Line is missing. Please fill in and continue.'))

            if rec.category == 'entertainment' and len(rec.request_line_ids.mapped('project_id')) > 1:
                raise UserError(
                    _('You cannot submit a purchase request with multiple projects when category is Entertainment.'))

    # Check remained amount of budget code is enough to request purchase
    def _check_budgets(self):
        # Search opening budget year (only 1 opened at the same time)
        open_budget_year = self.env['budget.analytic.year'].search(
            [('state', '=', 'confirmed'), ('company_id', '=', self.company_id.id)], limit=1)
        if not open_budget_year:
            raise ValidationError('Cannot find the Budget Year. Please check!')
        budget_line_year_ids = open_budget_year.budget_line_year_ids
        for budget_code, request_lines in groupby(self.request_line_ids, lambda l: l.analytic_account_id):
            request_lines = self.env["request.purchase.line"].concat(
                *request_lines)
            # Get the budget line of budget year based on budget code
            check_budget_line = budget_line_year_ids.filtered_domain(
                [('account_id', '=', budget_code.id)])
            total_amount = sum(request_lines.mapped('price_total'))
            if total_amount > check_budget_line.remained_amount:
                product_name = ', '.join(request_lines.mapped('product_id.name'))
                err_msg = f"""
                The amount of product/service has exceeded the remaining budget.

                - The amount of product/service "{product_name}" has exceeded the remaining budget "{budget_code.name} - ID: {budget_code.id}".
                """
                raise ValidationError(err_msg)

    def _prepare_account_payment_vals(self):
        self.ensure_one()

        return {
            'partner_id': self.vendor_id.id,
            'company_id': self.company_id.id,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'memo': self.name,
            'amount': sum(self.request_line_ids.mapped("price_total")),
            'request_purchase_id': self.id
        }
    
    def _prepare_account_move_vals(self):
        self.ensure_one()

        return {
            'partner_id': self.vendor_id.id,
            'move_type': 'in_invoice',
            'paid_by': 'company',
            'request_purchase_id': self.id,
            'is_request_payment': True,
            'invoice_line_ids': [Command.create({
                'product_id': line.product_id.id,
                'quantity': line.qty_demand,
                'name': line.description,
                'price_unit': line.price_unit,
                'product_uom_id': line.product_uom_id.id,
                'price_subtotal': line.price_total,
                'request_purchase_line_id': line.id,
                'analytic_distribution': {line.analytic_account_id.id: 100}
            }) for line in self.request_line_ids],
        }

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence'].with_context(
            month_sequence=True).sudo()
        for vals in vals_list:
            if vals.get("frequency") == "recursive" and vals.get("number_of_months", 0) <= 0:
                raise UserError(_("Number of months should be larger than 0"))
            vals['name'] = IrSequence.next_by_code('request.purchase')
        return super(RequestPurchase, self).create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        for request in self:
            if request.frequency == "recursive" and request.number_of_months <= 0:
                raise UserError(_("Number of months should be larger than 0"))
        return res

    def _action_create_budget_reserved(self):
        BudgetReservedEnv = self.env['budget.reserved'].sudo()
        budget_reserved_lines = []
        for request in self:
            budget_reserved_lines.extend(request._prepare_budget_reserved_lines())

        BudgetReservedEnv.search([
            ('request_purchase_id', 'in', self.ids)
        ]).unlink()
        BudgetReservedEnv.create(budget_reserved_lines)

    def _prepare_budget_reserved_lines(self):
        self.ensure_one()
        budget_reserved_lines = [{
            'account_id': account.id,
            'request_purchase_id': self.id,
            'company_id': self.company_id.id,
        } for account in self.request_line_ids.mapped('analytic_account_id')]

        return budget_reserved_lines
