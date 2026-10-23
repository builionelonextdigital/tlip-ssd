from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError


class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    def _create_activity(self):
        vendor_selection_approvers = self.filtered(lambda r: r.request_id.related_model == 'task.order.selection')
        for approver in vendor_selection_approvers:
            request = approver.request_id
            related_record = self.env[request.related_model].browse(
                request.related_res_id
            ).exists()
            users = approver.user_id or approver.job_id.employee_ids.user_id.filtered_domain([("active", "=", True)])
            for user in users:
                related_record.task_id.activity_schedule(
                    'approvals.mail_activity_data_approval',
                    user_id=user.id)
        super(ApprovalApprover, self - vendor_selection_approvers)._create_activity()
