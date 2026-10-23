from odoo import models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def _compute_can_write(self):
        activity_type_id = self.env.ref('approvals.mail_activity_data_approval').id
        approval_activities = self.filtered(
            lambda ac: ac.activity_type_id.id == activity_type_id)

        approval_activities.can_write = False
        super(MailActivity, self - approval_activities)._compute_can_write()
