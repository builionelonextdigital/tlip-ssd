from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    related_model = fields.Char(
        related='category_id.related_model', string='Related Model')
    related_res_id = fields.Many2oneReference(
        string='Related Document ID', index=True, model_field='related_model')
    related_res_name = fields.Char(
        string='Document Name',
        compute='_compute_non_stored_information_from_related_document',
        compute_sudo=True,)
    withdraw_reason = fields.Text("Reason", readonly=True)
    approval_minimum = fields.Integer(
        string='Minimum Approvers', default=0, copy=False,
        help="Số người duyệt tối thiểu để request được chấp thuận")
    approval_review_ids = fields.One2many(
        'approval.review', 'approval_request_id', string='Reviews')
    to_review_contract = fields.Boolean(
        related='category_id.to_review_contract')
    approver_sequence = fields.Boolean(related=False, store=True)
    credit_account_ids = fields.Many2many(
        comodel_name='account.account',
        relation='approval_request_credit_account_ref',
        compute='_compute_stored_information_from_related_document',
        string='Credit Accounts',
        store=True,
    )
    debit_account_ids = fields.Many2many(
        comodel_name='account.account',
        relation='approval_request_debit_account_ref',
        compute='_compute_stored_information_from_related_document',
        string='Debit Accounts',
        store=True,
    )

    @api.depends('related_model', 'related_res_id')
    def _compute_stored_information_from_related_document(self):
        for rec in self:
            amount = 0
            credit_account_ids = []
            debit_account_ids = []
            partner_id = False

            related_model = rec.related_model
            if related_model and related_model in self.env:
                related_record = self.env[related_model].browse(
                    rec.related_res_id
                ).exists()

                if related_record:
                    if related_model in ['account.move', 'account.payment']:
                        # Identify Document Source Type
                        is_journal_entry = related_model == 'account.move'
                        # Get the corressponding lines
                        journal_items = related_record.line_ids \
                            if is_journal_entry \
                            else related_record.move_id.line_ids
                        # Get Credit and Debit Accounts
                        credit_account_ids = journal_items.filtered(
                            lambda line: line.credit != 0).account_id.ids
                        debit_account_ids = journal_items.filtered(
                            lambda line: line.debit != 0).account_id.ids
                        # Get Amount
                        amount = related_record.amount_total \
                            if is_journal_entry \
                            else related_record.amount
                        # Get Partner
                        partner_id = related_record.partner_id.id
                    else:
                        partner_id = hasattr(
                            related_record, 'partner_id') and related_record.partner_id.id or False
                        amount = hasattr(
                            related_record, 'amount') and related_record.amount or 0

            rec.write({
                'amount': amount,
                'credit_account_ids': [Command.set(credit_account_ids)],
                'debit_account_ids': [Command.set(debit_account_ids)],
                'partner_id': partner_id,
            })

    @api.depends('related_model', 'related_res_id')
    def _compute_non_stored_information_from_related_document(self):
        for rec in self:
            # Set up base value
            related_res_name = False

            # Get related information
            related_model = rec.related_model
            related_res_id = rec.related_res_id

            if related_model and related_model in self.env:
                related_record = self.env[related_model].browse(
                    related_res_id
                ).exists()

                if related_record:
                    related_res_name = related_record.display_name

            rec.related_res_name = related_res_name

    def _check_approver_ids(self):
        # Approver may have either User or Job Position so no need to check here.
        pass

    @api.depends_context('uid')
    @api.depends('approver_ids.status')
    def _compute_user_status(self):
        for approval in self:
            approvers = approval.approver_ids.filtered(
                lambda approver: self.env.user in approver.user_ids)
            pending_approvers = approvers.filtered(
                lambda approver: approver.status == 'pending')
            reviewed_approvers = approvers.filtered(
                lambda approver: approver.status in ['approved', 'refused'])

            if len(pending_approvers) >= 1:
                approvers = pending_approvers
            elif len(reviewed_approvers) >= 1:
                approvers = reviewed_approvers

            approval.user_status = approvers and approvers[0].status

    def _ensure_can_approve(self):
        super()._ensure_can_approve()
        for approval in self:
            if approval.request_status in ['approved', 'refused', 'cancel'] and not approval.to_review_contract:
                raise ValidationError(
                    _('Cannot approve request (%s) that is already %s.', approval.name, approval.request_status))

            if approval.user_status != 'pending':
                raise ValidationError(
                    _('(%s) You can only approve requests that are pending for your approval.', approval.name))

    def _trigger_approve_or_refuse_review(self, approver):
        if not self.filtered('to_review_contract'):
            return
        review_status = 'refused' if self.env.context.get(
            'review_contract_refuse') else 'approved'
        approver.write({'review_status': review_status})

    def action_confirm(self):
        self = self.sudo()
        res = super().action_confirm()
        if self.to_review_contract:
            approvers = self.approver_ids
            if self.approver_sequence:
                for approver in self.approver_ids:
                    approver.write({'review_status': approver.status})
            else:
                pending_approvers = approvers.filtered(
                    lambda a: a.status == 'pending')
                pending_approvers.write({'review_status': 'pending'})
        return res

    def action_approve(self, approver=None):
        approver = self._validate_approve_reject(approver)
        minimum = self._get_required_approver_count()
        other_approved = self.approver_ids.filtered(
            lambda a: a.status == 'approved' and a != approver)
        if len(other_approved) + 1 < minimum:
            approver.write({'status': 'approved'})
            self._trigger_approve_or_refuse_review(approver)
            return True
        self = self.sudo()

        # Retrieve existing approval activities before creating new ones
        prev_approval_activities = self._get_existing_approval_activities()

        result = super().action_approve(approver=approver)

        # Trigger run action approve mixin and approve approval request
        self._handle_post_approved_actions(approver, prev_approval_activities)

        return result

    def action_refuse(self, approver=None):
        self = self.sudo()
        approver = self._validate_approve_reject(approver)

        result = super().action_refuse(approver=approver)

        # Trigger run action refuse mixin
        self._handle_post_rejected_actions()

        return result

    def action_cancel(self):
        self = self.sudo()
        result = super().action_cancel()
        
        self._handle_post_cancelled_actions()

        return result

    def action_withdraw(self, approver=None):
        self = self.sudo()
        approver = self._validate_approve_reject(approver)

        result = super().action_withdraw(approver=approver)
        # TODO: handle withdraw
        approver.write({'review_status': 'pending'})
        return result

    def action_withdraw_with_reason(self, reason: str):
        for request in self:
            if request.request_owner_id != self.env.user and not self.env.user.has_group('base.group_system'):
                raise ValidationError(_("Only the request owner can withdraw this request"))
            if request.request_status not in ('pending', 'new'):
                raise ValidationError(_("Only pending requests can be withdrawn"))
        self.write({"withdraw_reason": reason})
        self._send_withdraw_email_notification(reason)
        self.action_cancel()

    def _get_required_approver_count(self):
        self.ensure_one()
        options = self.category_id.approval_option_ids
        minimum = max(options.mapped('approval_minimum') or [0]) or 0
        required = len(self.approver_ids.filtered(lambda a: a.required))
        return max(minimum, required, 1)

    def action_open_related_document(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/odoo/{self.related_model}/{self.related_res_id}',
            'target': '_blank',
        }
    
    def _validate_approve_reject(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approvers = self.mapped('approver_ids').filtered(
                lambda approver: self.env.user in approver.user_ids and approver.status == 'pending')
            approver = approvers and approvers[0]
        if not approver:
            raise ValidationError(_("You cannot approve/refuse on this request"))
        return approver

    def _handle_post_approved_actions(self, approver, prev_approval_activities):
        """
        Handle post-approved actions, such as triggering reviews and unlinking activities.
        """
        self._trigger_approve_or_refuse_review(approver)

        for approval in self:
            record = approval._get_related_record()
            if record and approval.request_status == 'approved':
                record.with_context(approver_job=approver.job_id.id)._trigger_action_approve()

            # Unlink all previous activities related to the latest approved approver
            approval._unlink_approval_activities(record or self, prev_approval_activities)

    def _handle_post_rejected_actions(self):
        """
        Handle actions to be performed after the approval request is refused.
        """
        for approval in self:
            record = approval._get_related_record()
            if record and approval.request_status == 'refused':
                # Trigger the refusal action on the related record
                record._trigger_action_refuse()

            # Remove all activities associated with the related record and approval request
            record.activity_ids.unlink()
            approval.activity_ids.unlink()

    def _handle_post_cancelled_actions(self):
        """
        Handle actions to be performed after the approval request is refused.
        """
        # Update review status if needed
        self.filtered(lambda r: r.to_review_contract).mapped(
            'approver_ids').write({'review_status': 'cancel'})

        for approval in self:
            record = approval._get_related_record()
            if record and approval.request_status == 'cancel':
                # Trigger the cancellation action on the related record
                record._trigger_action_cancel()

            # Remove all activities associated with the related record and approval request
            record.activity_ids.unlink()
            approval.activity_ids.unlink()

    def _get_related_record(self):
        self.ensure_one()
        if self.related_res_id and self.related_model:
            return self.env[self.related_model].browse(self.related_res_id)

        return self.env['approval.request']

    def _send_withdraw_email_notification(self, reason: str):
        for approval in self:
            body = _("%(request_name)s created on %(create_date)s by %(request_owner)s has been withdraw with reason %(reason)s",
                     reason=reason,
                     request_name=approval.name,
                     create_date=approval.create_date.date(),
                     request_owner=approval.request_owner_id.name)
            subject = _("%(request_name)s of %(request_owner)s has been withdraw",
                        request_name=approval.name,
                        request_owner=approval.request_owner_id.name)
            approved_approvers = approval.approver_ids.filtered(
                lambda approver: approver.status == 'approved')
            approval.message_notify(
                body=body,
                subject=subject,
                partner_ids=approved_approvers.user_id.partner_id.ids,
            )

    def _get_existing_approval_activities(self):
        # Retrieve the current approval-related mail activities for the records.
        current_activities = self.env['mail.activity']
        activity_type_id = self.env.ref('approvals.mail_activity_data_approval', raise_if_not_found=False).id
        if not activity_type_id:
            return current_activities

        for approval in self:
            record = approval._get_related_record() or approval
            domain = [
                ('res_model', '=', record._name),
                ('res_id', 'in', record.ids),
                ('activity_type_id', '=', activity_type_id)
            ]
            # Search and accumulate activities
            current_activities |= self.env['mail.activity'].search(domain)

        return current_activities

    def _unlink_approval_activities(self, record, prev_approval_activities=None):
        self.ensure_one()
        activity_type_id = self.env.ref('approvals.mail_activity_data_approval', raise_if_not_found=False).id
        if not activity_type_id:
            return

        prev_approval_activities = prev_approval_activities or self.env['mail.activity']
        latest_approval_line = self.approver_ids.filtered(lambda l: l.status in ('approved', 'refused'))
        if latest_approval_line:
            latest_approval_line = latest_approval_line[-1]
            domain = [
                ('res_model', '=', record._name),
                ('res_id', 'in', record.ids),
                ('activity_type_id', '=', activity_type_id),
                ('user_id', 'in', latest_approval_line.user_ids.ids)
            ]
            activities = prev_approval_activities.filtered_domain(domain)
            activities.unlink()


class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    user_id = fields.Many2one(required=False)
    job_id = fields.Many2one(
        'hr.job', ondelete='cascade', string="Job Position")
    user_ids = fields.Many2many(
        'res.users', compute="_compute_user_ids", compute_sudo=True)
    review_status = fields.Selection([
        ('pending', 'To Approve'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], string="Review Status", default=False)

    def _compute_user_ids(self):
        for rec in self:
            rec.user_ids = rec.user_id or rec.job_id.mapped(
                'employee_ids.user_id')

    def _create_activity(self):
        for approver in self:
            request = approver.request_id
            related_record = self.env[request.related_model].browse(
                request.related_res_id
            ).exists()
            users = approver.user_id or approver.job_id.employee_ids.user_id.filtered_domain([("active", "=", True)])
            related_record = related_record.with_context(skip_approver_subscribe=True)
            for user in users:
                related_record.activity_schedule(
                    'approvals.mail_activity_data_approval',
                    user_id=user.id)

    def _get_employee(self):
        self.ensure_one()
        sign_user = self.user_id or self.env.user
        sign_employee = self.env['hr.employee'].search([
            ('user_id', '=', sign_user.id),
            ('company_id', '=', self.company_id.id),
            ('job_id', '!=', False),
            ('job_id', '=', self.job_id.id)
        ], limit=1)

        return sign_employee

    def write(self, vals):
        if 'status' in vals and vals['status'] in ('approved', 'refused'):
            vals['user_id'] = self.env.user.id
        return super().write(vals)
