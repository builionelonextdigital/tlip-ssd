from odoo import models, fields


class SubmitApprovalWizard(models.TransientModel):
    _name = "submit.approval.wizard"
    _description = "Submit Approval Wizard"

    name = fields.Char(required=True)
    category_id = fields.Many2one("approval.category")
    category_option_id = fields.Many2one("approval.category.option")
    related_res_id = fields.Integer()
    description = fields.Text("Description")
    identify_key = fields.Char()

    def action_submit_approval(self):
        self.ensure_one()
        request_value = {
            "name": self.name,
            "related_res_id": self.related_res_id,
            "reason": self.description,
            "request_status": "pending",
            "request_owner_id": self.env.user.id,
            "category_id": self.category_id.id,
            "approver_sequence": self.category_option_id.approver_sequence,
            "approval_minimum": self.category_option_id.approval_minimum or len(self.category_option_id.approver_ids),
            "approver_ids": [(0, 0, {
                "user_id": approver.user_id.id,
                "sequence": approver.sequence,
                "job_id": approver.job_id.id,
                "required": approver.required})
                for approver in self.category_option_id.approver_ids]
        }
        request = self.env["approval.request"].create(request_value)
        request.action_confirm()
        # trigger action after submit mixin
        related_record = self.env[self.category_id.related_model].browse(
            self.related_res_id)
        related_record.with_context(
            identify_key=self.identify_key)._trigger_action_after_submit(request)
