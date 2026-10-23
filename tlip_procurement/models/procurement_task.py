import base64
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import groupby
from odoo.tools.safe_eval import safe_eval


class ProcurementTask(models.Model):
    _name = "procurement.task"
    _description = "Procurement Task"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'approval.matrix.mixin']
    _order = 'priority desc, id desc'

    state = fields.Selection([
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("vendor_selection", "Vendor Selection"),
        ("contract_review", "Contract Review"),
        ("approved", "Approved"),
        ("canceled", "Canceled"),
        ("withdrawn", "Withdrawn"),
    ], string="Status", tracking=True, default="draft")
    name = fields.Char(
        string="Procurement Task", required=True, default="New",
        copy=False, index='trigram',
        tracking=True
    )
    priority = fields.Selection(selection=[
        ('0', 'Normal'), ('1', 'Urgent')],
        string='Priority', default='0'
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        check_company=True, copy=False, tracking=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company.id,
        required=True, index=True,
        ondelete="cascade"
    )
    date_order = fields.Datetime(
        string="Order Deadline", tracking=True, required=True)
    date_planned = fields.Datetime(
        string="Expected Arrival", tracking=True, required=True)
    notes = fields.Text()
    amount_total = fields.Monetary(
        string="Total Amount", store=True, readonly=True, compute='_amount_all')
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        related='company_id.currency_id', store=True)
    request_line_ids = fields.One2many(
        comodel_name='request.purchase.line', inverse_name="task_id",
    )
    po_ids = fields.One2many(
        comodel_name='purchase.order', inverse_name="task_id",
    )
    count_rfq = fields.Integer(compute="_compute_count_po")
    count_po = fields.Integer(compute="_compute_count_po")
    rfq_selection_ids = fields.One2many(
        comodel_name='task.order.selection', inverse_name="task_id",
    )
    count_rfq_selections = fields.Integer(compute="_compute_rfq_selections")
    select_bidding = fields.Selection(selection=[
        ('bidding', 'Bidding'),
        ('non_bidding', 'Non-Bidding')], string='Bidding/Non-Bidding')
    requirement_line_ids = fields.One2many(
        'request.purchase.requirement.line', 'procurement_task_id')
    non_bidding_reason = fields.Char('Non-Bidding Reason')
    purchase_contract_type_id = fields.Many2one(
        'purchase.contract.type', 'Contract Type', tracking=True)
    vendor_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Suppliers",
        check_company=True,
        domain="[('vendor_state', '=', 'approved'), ('is_blocked', '=', False)]",
        required=True
    )
    checklist = fields.Html(
        name='Checklist', compute="_compute_checklist_template", store=True, readonly=False)
    budget_department_responsible_id = fields.Many2one(
        "res.users",
        compute="_compute_budget_department_responsible",
        compute_sudo=True,
        store=True,
        string="Budget Department PIC",
    )
    budget_department_responsible_job_id = fields.Many2one('hr.job',
                                                           compute="_compute_budget_department_responsible",
                                                           compute_sudo=True,
                                                           store=True)
    confirmed_selection_id = fields.Many2one(
        'task.order.selection',
        compute="_compute_rfq_selections")
    current_contract_id = fields.Many2one(
        comodel_name='purchase.requisition',
        compute="_compute_current_contract_id", store=True, readonly=False)
    show_preference_check = fields.Boolean(
        compute="_compute_rfq_selections")
    fs_annual_sales = fields.Float(
        compute="_compute_rfq_selections")
    fs_annual_pat = fields.Float(
        compute="_compute_rfq_selections")
    fs_total_assets = fields.Float(
        compute="_compute_rfq_selections")
    copy_fs_file = fields.Binary(
        string='Copy FS attachment', compute="_compute_rfq_selections")
    copy_fs_filename = fields.Char(
        compute="_compute_rfq_selections")
    copy_client_file = fields.Binary(
        string='Copy Client list', compute="_compute_rfq_selections")
    copy_client_filename = fields.Char(
        compute="_compute_rfq_selections")
    site_check_file = fields.Binary(
        string='Site Check report', compute="_compute_rfq_selections")
    site_check_filename = fields.Char(
        compute="_compute_rfq_selections")
    result_site_check = fields.Char(
        string='Result of Site Check',
        compute="_compute_rfq_selections")
    other_notes = fields.Char(
        string='Other notes',
        compute="_compute_rfq_selections")
    currency_id = fields.Many2one(
        comodel_name='res.currency', compute="_compute_rfq_selections")
    request_type = fields.Selection(selection=[
        ('normal', 'Normal'),
        ('special', 'Special'),
        ('special_auth', 'Special - Authority')
    ], string="Request Type", compute="_compute_request_type", store=True
    )
    procurement_user_ids = fields.Many2many("res.users",
                                            compute="_compute_procurement_users")
    cancel_reason = fields.Text(string="Reason for Cancellation")
    is_advance_enabled = fields.Boolean(string='Advance Payment', default=False)
    bypass_vendor_selection_rule = fields.Boolean(string="Bypass Vendor Selection Rule")
    analytic_line_ids = fields.One2many(
        'account.analytic.line', 'task_id', string='Analytic Lines')
    is_locked = fields.Boolean(string='Is Locked')

    @api.depends("request_line_ids.price_total")
    def _amount_all(self):
        self.mapped("request_line_ids")
        for rec in self:
            rec.amount_total = sum(rec.request_line_ids.mapped("price_total"))

    def _compute_count_po(self):
        for rec in self:
            po_ids = rec.po_ids
            rfqs = po_ids.filtered_domain([('is_order', '=', False)])
            count_rfq = len(rfqs)
            count_po = len(po_ids) - count_rfq

            rec.count_rfq = count_rfq
            rec.count_po = count_po

    @api.depends("rfq_selection_ids", "rfq_selection_ids.state")
    def _compute_rfq_selections(self):
        task_fields_mapping = [
            ('show_preference_check', 'show_preference_check'),
            ('fs_annual_sales', 'fs_annual_sales'),
            ('fs_annual_pat', 'fs_annual_pat'),
            ('fs_total_assets', 'fs_total_assets'),
            ('copy_fs_file', 'copy_fs_file'),
            ('copy_fs_filename', 'copy_fs_filename'),
            ('copy_client_file', 'copy_client_file'),
            ('copy_client_filename', 'copy_client_filename'),
            ('site_check_file', 'site_check_file'),
            ('site_check_filename', 'site_check_filename'),
            ('result_site_check', 'result_site_check'),
            ('other_notes', 'other_notes'),
            ('currency_id', 'currency_id'),
        ]
        for rec in self:
            rfq_selection_ids = rec.rfq_selection_ids
            confirmed_selection_ids = rfq_selection_ids.filtered_domain(
                [("state", "=", "confirmed")]
            )
            confirmed_selection = confirmed_selection_ids[:1]
            # update data computed
            rec.count_rfq_selections = len(rfq_selection_ids)
            rec.confirmed_selection_id = confirmed_selection
            for field, selection_field in task_fields_mapping:
                rec[field] = confirmed_selection[selection_field]

    @api.depends("rfq_selection_ids.requisition_id")
    def _compute_current_contract_id(self):
        for rec in self:
            confirmed_selection_ids = rec.rfq_selection_ids.filtered_domain(
                [("state", "=", "confirmed")]
            )
            confirmed_selection = confirmed_selection_ids[:1]
            rec.current_contract_id = confirmed_selection.requisition_id

    @api.depends('state')
    def _compute_checklist_template(self):
        update_checklist_tasks = self.filtered_domain([
            ('state', 'in', ['vendor_selection', 'contract_review'])
        ])
        if update_checklist_tasks:
            checklist_templates = self.env['checklist.template'].search([
                ('state', '=', 'confirm'),
                ('related_model_id.model', '=', self[:1]._name)
            ])
            for task in update_checklist_tasks:
                task_checklist = False
                for checklist in checklist_templates:
                    checklist_condition = safe_eval(checklist.condition)
                    if task.filtered_domain(checklist_condition):
                        task_checklist = checklist.description
                        break

                task.checklist = task_checklist

        (self - update_checklist_tasks).checklist = False

    @api.depends("request_line_ids.budget_department_id")
    def _compute_budget_department_responsible(self):
        for rec in self:
            responsible_user = False
            request_lines = rec.request_line_ids
            if len(request_lines.budget_department_id) > 1:
                budget_department_group = request_lines.budget_department_group_id.with_context(
                    company_id=rec.company_id.id)
                # Ensure that procurement task line will have one budget department group
                employee = budget_department_group.job_id.employee_ids.filtered(
                    lambda r: r.company_id == rec.company_id)[:1]
                rec.budget_department_responsible_job_id = budget_department_group.job_id
                rec.budget_department_responsible_id = employee.user_id
            else:
                budget_department = request_lines.budget_department_id.with_context(
                    company_id=rec.company_id.id)
                employee = budget_department.job_id.employee_ids.filtered(
                    lambda r: r.company_id == rec.company_id)[:1]
                rec.budget_department_responsible_job_id = budget_department.job_id
                rec.budget_department_responsible_id = employee.user_id

    @api.depends("request_line_ids")
    def _compute_request_type(self):
        for rec in self:
            request_type = rec.request_type or "normal"
            request_id = rec.request_line_ids.request_id
            if len(request_id) == 1:
                request_type = request_id.request_type

            rec.request_type = request_type

    @api.depends_context('uid')
    def _compute_procurement_users(self):
        user_ids = []
        procurement_group = self.env.ref(
            'tlip_access_rights.group_tlip_procurement_user')
        if procurement_group:
            user_ids = procurement_group.users.ids
        for rec in self:
            rec.procurement_user_ids = [(6, 0, user_ids)]

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action['context']['default_name'] = _(
            f'Approval Procurement Task {self.name}')
        return action

    def action_confirm(self):
        self.write({'state': 'in_progress'})

    def action_create_rfqs(self):
        self.ensure_one()
        self.rfq_selection_ids.unlink()
        total_amount = sum(self.request_line_ids.mapped('price_total'))

        if not self.bypass_vendor_selection_rule:
            # User has favorite vendor selection case.
            match_vendor_selection_rule = self.env['vendor.selection.rule'].search([
                ('minimum_amount', '<=', total_amount),
                '|',
                ('maximum_amount', '>=', total_amount),
                ('maximum_amount', '=', 0)
            ], limit=1)
            if not match_vendor_selection_rule:
                raise UserError(
                    _("Please set up Vendor Selection Rule before create RFQ."))
            if len(self.vendor_ids) < match_vendor_selection_rule.minimum_selected_vendors:
                raise UserError(
                    _(f"Please select at least {match_vendor_selection_rule.minimum_selected_vendors} Vendor(s)."))

        purchase_orders = self.env["purchase.order"].create(
            self._prepare_purchase_order_vals())
        self.env["task.order.selection"].create(
            self._prepare_task_order_selection_vals(purchase_orders))
        self.write({'state': 'vendor_selection'})
        return self.action_view_rfqs()

    def _prepare_task_order_selection_vals(self, purchase_orders):
        return [{
            "po_id": po.id,
            "task_id": self.id
        } for po in purchase_orders]

    def _prepare_purchase_order_vals(self):
        company = self.company_id
        order_vals = {
            "user_id": self.user_id.id,
            "date_order": self.date_order,
            "order_line": self._prepare_purchase_order_line_vals(),
            "company_id": company.id,
            "origin": ", ".join(self.request_line_ids.request_id.mapped("name")),
            "task_id": self.id,
            "requirement_line_ids": [(0, 0, {'name': req.name, 'description': req.description})
                                     for req in self.requirement_line_ids],
            "is_order": False
        }
        return [{
            'partner_id': vendor.id,
            'payment_term_id': vendor.with_company(company).property_supplier_payment_term_id.id,
            **order_vals
        } for vendor in self.vendor_ids]

    def _prepare_purchase_order_line_vals(self):
        order_line_vals = []
        for request_line in self.request_line_ids.filtered(lambda l: l.product_id):
            qty_demand = request_line.qty_demand
            analytic_distribution = self._get_analytic_distribution(
                request_line, qty_demand)
            order_line_vals.append((0, 0, {
                "product_id": request_line.product_id.id,
                "name": request_line.description,
                "price_unit": request_line.price_unit,
                "product_qty": qty_demand,
                "analytic_distribution": analytic_distribution,
                "product_uom": request_line.product_uom_id.id,
                "origin": request_line.description,
                "request_line_id": request_line.id
            }))
        return order_line_vals

    def _get_analytic_distribution(self, request_lines, total_qty_demand):
        analytic_distribution = defaultdict(int)
        for line in request_lines:
            analytic_distribution[line.analytic_account_id.id] += (
                total_qty_demand and (line.qty_demand / total_qty_demand * 100))
        return analytic_distribution

    def action_save_view_assign_task(self):
        self.ensure_one()
        # Create activity to inform responsible user
        if self.user_id != self.env.user:
            activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            res_model_id = self.env.ref(
                "tlip_procurement.model_procurement_task").id
            activity_vals = {
                'activity_type_id': activity_type_id,
                'user_id': self.user_id.id,
                'res_id': self.id,
                'res_model_id': res_model_id,
                'summary': _(f"Procurement Task {self.name} is assigned for you.")
            }
            self.env["mail.activity"].create(activity_vals)
        # Open new task that created and assigned for responsible
        action = self.env['ir.actions.actions']._for_xml_id(
            'tlip_procurement.procurement_task_action')
        action.update({
            'views': [[self.env.ref('tlip_procurement.procurement_task_view_form').id, "form"]],
            'res_id': self.id
        })
        return action

    def action_reset(self):
        self.rfq_selection_ids.unlink()
        rfq_orders = self.po_ids.filtered_domain([('is_order', '=', False)])
        rfq_orders.button_cancel()
        rfq_orders.unlink()
        self.write({
            'state': 'draft',
            'approval_request_id': False,
        })

    def button_cancel(self):
        self.write({'cancel_reason': False})
        ctx = dict(self.env.context)
        return {
            'name': _('Cancel'),
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_model': 'procurement.task',
            'view_id': self.env.ref('tlip_procurement.procurement_task_cancel_reason_view_form').id,
            "view_type": "form",
            "view_mode": "form",
            'res_id': self.id,
            'context': ctx
        }

    def action_cancel(self):
        self.message_post(body=_(
            f"{self._description} ({self.display_name}) was cancelled with reason: {self.cancel_reason}"))

        self.write({'state': 'canceled'})

        # Automatically cancel request line if special request
        if self.request_type == "special":
            request = self.request_line_ids.request_id
            request.action_cancel()
            request.message_post(body=_(
                f"({request.name}) was automatically cancelled from task ({self.display_name}) with reason: {self.cancel_reason}"
            ))

        # Unlink all request items, user has to re-create the task
        self.request_line_ids.write({'task_id': False})

    def action_review_contract(self):
        self.write({'state': 'contract_review'})

    def action_view_rfqs(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'purchase.purchase_rfq')
        action['domain'] = [('task_id', '=', self.id),
                            ('is_order', '=', False)]
        action['context'] = {'create': 0}
        return action

    def action_view_purchase_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'purchase.purchase_form_action')
        if self.count_po == 1:
            action.update({
                "res_id": self.po_ids.filtered_domain([('is_order', '=', True)]).id,
                "view_mode": 'form',
                'views': [(self.env.ref('purchase.purchase_order_form').id, 'form')],
            })
        else:
            action.update({
                "domain": [('task_id', '=', self.id), ('is_order', '=', True)],
                "view_mode": 'tree,form'
            })
        return action

    def action_view_requisition_agreements(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'tlip_procurement.action_purchase_contract_view')
        related_contracts = self.env['purchase.requisition'].with_context(active_test=False).search(
            [('task_id', '=', self.id)])
        if len(related_contracts) == 1:
            action.update({
                'res_id': related_contracts.id,
                'view_mode': 'form',
                'views': [(self.env.ref('tlip_procurement.purchase_contract_view_form').id, 'form')],
                'context': {'create': 0}
            })
        else:
            action.update({
                'domain': [('id', 'in', related_contracts.ids)],
                'context': {
                    'create': 0,
                    'active_test': False,
                    'show_active_boolean': True
                }
            })
        return action

    def action_preview_vendor_evaluation(self):
        self.ensure_one()
        pdf_report = self.env.ref(
            'tlip_procurement.action_report_vendor_evaluation')
        content = self.env['ir.actions.report']._render_qweb_pdf(
            pdf_report.report_name,
            res_ids=self.id,
        )[0]

        wizard = self.env['document.preview'].create({
            'file': base64.b64encode(content)
        })
        return {
            'name': _(f'Vendor Evaluation Sheet {self.name}'),
            'view_mode': 'form',
            'res_model': 'document.preview',
            'res_id': wizard.id,
            'views': [(self.env.ref('tlip_base.document_preview_wizard_form_view').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(self.env.context)
        }

    def action_lock_budget(self):
        self.ensure_one()
        if self.is_locked:
            raise UserError(_("This contract is already locked."))
        if self.state != 'approved' or self.current_contract_id:
            raise UserError(_("Only procurement task with bypass contract can be locked."))

        purchases = self.po_ids.filtered_domain([('is_order', '=', True)])
        if purchases.filtered(lambda p: p.state not in ('purchase', 'done', 'cancel')):
            raise UserError(_("You cannot lock contract with in-progress Purchase Order(s)"))
        purchases = purchases.filtered(lambda p: 
            bool(p.picking_ids.filtered(lambda s: s.state not in ('done', 'cancel'))) or 
            bool(p.invoice_ids.filtered(lambda inv: inv.state not in ('posted', 'cancel')))
        )
        if purchases:
            order_names = ', '.join(purchases.mapped('name'))
            raise UserError(_("This contract still has a purchase order %s that needs to be received or posted/cancelled to the vendor bills." % order_names))

        self.write({"is_locked": True})
        self.env['budget.reserved'].action_unreserved_amount(tasks=self)

    def _trigger_action_approve(self):
        self.write({'state': 'approved'})
        self.current_contract_id.write({'state': 'done'})

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval',
        })

        for selection in self.rfq_selection_ids:
            # Only applied when bypass contract
            if selection.confirm_wizard_vals:
                selection.with_context(
                    approval_submission=True).action_confirm()
                break
        return result

    def _validate_submit_approval(self):
        if self.filtered(lambda r: not r.rfq_selection_ids):
            raise UserError(
                _("Proposed RFQ's is missing. Please fill in and continue"))

    def action_approve_request(self):
        prev_approval_activities = self._get_existing_approval_activities()
        result = super().action_approve_request()
        approval = self.approval_request_id
        # switch activities to procurement task
        if approval.related_model == 'task.order.selection':
            selection = self.env['task.order.selection'].browse(
                approval.related_res_id)
            activities = selection.activity_ids
            approval._unlink_approval_activities(self, prev_approval_activities)
            model_id = self.env['ir.model']._get(self._name).id
            activities.write({'res_model_id': model_id, 'res_id': self.id})
        return result

    def action_reject_request(self):
        prev_approval_activities = self._get_existing_approval_activities()
        result = super().action_reject_request()
        approval = self.approval_request_id
        # switch activities to procurement task
        if approval.related_model == 'task.order.selection':
            selection = self.env['task.order.selection'].browse(
                approval.related_res_id)
            activities = selection.activity_ids
            approval._unlink_approval_activities(self, prev_approval_activities)
            model_id = self.env['ir.model']._get(self._name).id
            activities.write({'res_model_id': model_id, 'res_id': self.id})
        return result

    def _get_existing_approval_activities(self):
        self.ensure_one()
        # Retrieve the current approval-related mail activities for the records.
        activity_type_id = self.env.ref('approvals.mail_activity_data_approval', raise_if_not_found=False).id
        if not activity_type_id:
            return self.env['mail.activity']

        # Search and accumulate activities
        return self.env['mail.activity'].search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', activity_type_id)
        ])

    def _action_done(self):
        self.ensure_one()
        self.write({'state': 'done'})

    def action_create_purchase_order(self):
        self.ensure_one()
        order = self.confirmed_selection_id.po_id.copy(
            {'is_order': True, 'task_id': self.id})
        action = self.env['ir.actions.act_window']._for_xml_id(
            'purchase_requisition.action_purchase_requisition_to_so')
        action.update({
            'res_id': order.id,
            'views': [(False, 'form')],
            "view_mode": "form",
            "view_type": "form",
            "target": "current"
        })
        return action

    def _trigger_action_withdraw(self, reason: str):
        super()._trigger_action_withdraw(reason)

        self.write({'state': 'withdrawn'})
        
        # Cancel related records: rfq and rfq selections
        self.po_ids.button_cancel()
        self.current_contract_id.action_cancel()

        # Withdraw approval request from task order selection
        rfq_selections = self.rfq_selection_ids
        rfq_selections.action_cancel()

        # Remove approval activities on task
        activity_type_id = self.env.ref(
            'approvals.mail_activity_data_approval').id
        self.activity_ids.filtered(
            lambda ac: ac.activity_type_id.id == activity_type_id).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence'].with_context(
            month_sequence=True).sudo()
        for vals in vals_list:
            vals['name'] = IrSequence.next_by_code('procurement.task')
        return super(ProcurementTask, self).create(vals_list)
