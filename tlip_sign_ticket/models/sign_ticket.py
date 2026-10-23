from odoo import _, fields, models


class SignTicket(models.Model):
    _name = "sign.ticket"
    _inherit = ["sign.ticket", "approval.matrix.mixin"]

    signing_type = fields.Selection(default="mysign")

    # ------------------------------------------------------------------
    # Approval matrix
    # ------------------------------------------------------------------

    def _trigger_action_after_submit(self, request):
        """Link the approval request and sync signers from its approvers."""
        super()._trigger_action_after_submit(request)
        self.signer_line_ids.unlink()
        signer_vals = [
            {"ticket_id": self.id, "approver_id": approver.id}
            for approver in request.approver_ids.sorted("sequence")
        ]
        if signer_vals:
            self.env["sign.ticket.signer"].create(signer_vals)
        self.action_submit()

    def _trigger_action_withdraw(self, reason: str):
        super()._trigger_action_withdraw(reason)
        self.action_withdraw()

    def action_approve(self):
        for record in self:
            record.approval_request_id._validate_approve_reject(approver=record.current_approver_id)
        return super().action_approve()

    def action_reject(self):
        self.approval_request_id._validate_approve_reject(approver=self.current_approver_id)
        self.current_signer_id.write({'user_id': self.env.user.id})
        res = super().action_reject()
        return res

    def action_submit_approval(self):
        self.with_context(skip_signer_validation=True)._validate_action_submit()
        action = super().action_submit_approval()
        if action and isinstance(action, dict) and action.get('type') == 'ir.actions.act_window':
            action['context'].update({
                'default_name': _(f"Approval Sign Ticket {self.name}"),
                'default_description': self.note,
            })
        return action
