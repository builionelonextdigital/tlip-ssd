import ast
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalMatrixMixin(models.AbstractModel):
    _name = 'approval.matrix.mixin'
    _description = 'Approval Matrix Mixin'

    approval_request_id = fields.Many2one(
        'approval.request', copy=False)
    current_approver_id = fields.Many2one('approval.approver', string='Current Approver', compute='_compute_current_approver_id', store=True)
    request_owner_id = fields.Many2one(
        'res.users', related='approval_request_id.request_owner_id', string='Request Owner')
    request_reason = fields.Html(
        related='approval_request_id.reason', string='Request Description')
    approver_ids = fields.Many2many('approval.approver', string="Approvers",
                                    compute='_compute_approver_users', store=True, readonly=False, copy=False)
    approver_user_ids = fields.Many2many(
        "res.users", compute="_compute_approver_users", store=True, copy=False)
    history_approvals_count = fields.Integer(
        compute="_compute_history_approval")
    user_status = fields.Selection(related='approval_request_id.user_status')
    approval_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
        ],
        default="draft", tracking=True, copy=False,
    )

    @api.depends('approval_request_id', 'approval_request_id.approver_ids', 'approval_request_id.approver_ids.status')
    def _compute_current_approver_id(self):
        for record in self:
            approvers = record.approval_request_id.approver_ids.filtered(lambda r: r.status == 'pending')
            if approvers:
                record.current_approver_id = approvers[0]
            else:
                record.current_approver_id = False
        
    @api.depends('approval_request_id', 'approval_request_id.approver_ids')
    def _compute_approver_users(self):
        for rec in self:
            approvers = rec.approval_request_id.approver_ids
            rec.approver_ids = approvers
            rec.approver_user_ids = approvers.mapped(
                'user_ids')

    def _compute_history_approval(self):
        for rec in self:
            related_approval_count = self.env['approval.request'].search_count([
                ('related_model', '=', rec._name),
                ('related_res_id', '=', rec.id)])
            rec.history_approvals_count = related_approval_count

    def action_approve_request(self):
        self.ensure_one()
        self.approval_request_id.action_approve()

    def action_reject_request(self):
        self.ensure_one()
        self.approval_request_id.action_refuse()
        
    def action_reset_approval(self):
        self.write({"approval_state": "draft"})

    def action_submit_approval(self):
        self.ensure_one()
        selected_category, selected_option = self._find_matchable_approval_category()
        if not selected_category or not selected_option:
            # return self._trigger_action_approve()
            raise ValidationError(
                _("Cannot create approval request due to didn't find any match approval rules!"))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Submit Approval'),
            'res_model': 'submit.approval.wizard',
            'views': [(self.env.ref('tlip_approval.submit_approval_wizard_form').id, 'form')],
            'target': 'new',
            'context': {
                'default_related_res_id': self.id,
                'default_category_id': selected_category.id,
                'default_category_option_id': selected_option.id
            }
        }

    def action_withdraw_approval(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Withdraw'),
            'res_model': 'withdraw.approval.wizard',
            'views': [(self.env.ref('tlip_approval.withdraw_approval_wizard_form').id, 'form')],
            'target': 'new',
            'context': {
                'default_related_res_id': self.id,
                'default_related_model': self._name,
            }
        }

    def action_multi_approve_approval(self):
        for record in self:
            if record.user_status != 'pending':
                raise ValidationError(
                    _(f"You cannot approve for request {record.name}"))
            record.action_approve_request()

    def action_multi_submit_approval(self):
        wizard_vals = []
        for rec in self:
            action = rec.action_submit_approval()
            wizard_vals.append(
                rec._prepare_submit_approval_wizard_vals_from_action(action))

        for wizard in self.env['submit.approval.wizard'].create(wizard_vals):
            wizard.action_submit_approval()

    def _trigger_action_after_submit(self, request):
        self.write({'approval_request_id': request.id})

    def _find_matchable_approval_category(self):
        self.ensure_one()
        selected_category, selected_option = False, False
        domain = [('related_model', '=', self._name)]
        if getattr(self, 'company_id', False):
            domain.append(('company_id', '=?', self.company_id.id))
        categories = self.env['approval.category'].search(domain)
        for option in categories.mapped('approval_option_ids'):
            filter_domain = option.filter_domain
            if not filter_domain:
                filter_domain = '[]'
            try:
                if self.filtered_domain(ast.literal_eval(filter_domain)):
                    selected_category = option.category_id
                    selected_option = option
                    break
            except Exception as err:
                raise ValueError(err)
        return selected_category, selected_option

    def _trigger_action_approve(self):
        pass

    def _trigger_action_refuse(self):
        pass

    def _trigger_action_cancel(self):
        for record in self:
            if not record.approval_request_id:
                continue
            prev_approval_activities = record.approval_request_id._get_existing_approval_activities()
            record.approval_request_id._unlink_approval_activities(record, prev_approval_activities)

    def _trigger_action_withdraw(self, reason: str):
        self.message_post(body=_(
            f"{self._description} ({self.display_name}) was withdrawn with reason: {reason}"))
        self.approval_request_id.action_withdraw_with_reason(reason)

    def _prepare_submit_approval_wizard_vals_from_action(self, action):
        context = action.get('context', {})
        return {
            'name': context.get('default_name'),
            'category_id': context.get('default_category_id'),
            'category_option_id': context.get('default_category_option_id'),
            'related_res_id': context.get('default_related_res_id'),
            'description': context.get('default_description'),
            'identify_key': context.get('default_identify_key'),
        }

    def _get_final_approver_id(self):
        self.ensure_one()
        if not self.approver_ids:
            return self.env['approval.approver'].browse()

        final_approver = self.approver_ids[-1]
        return final_approver

    def _get_request_owner_id(self):
        self.ensure_one()
        request_user = self.approval_request_id.request_owner_id
        domain = [('user_id', '=', request_user.id)]
        if hasattr(self, 'company_id') and self.company_id:
            domain.append(('company_id', '=', self.company_id.id))

        employee = self.env['hr.employee'].search(domain, limit=1)
        return employee

    def action_open_approval_history_ids(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'approvals.approval_request_action_all')
        requests = self.env['approval.request'].search([('related_model', '=', self._name),
                                                        ('related_res_id', '=', self.id)])

        if len(requests) == 1:
            action.update({
                'res_id': requests.id,
                'view_mode': 'form',
                'views': [(False, 'form')]
            })
        elif requests:
            action['domain'] = [('related_model', '=', self._name),
                                ('related_res_id', '=', self.id)]
        else:
            raise ValidationError(
                _("No approval history found for this record!"))

        return action
