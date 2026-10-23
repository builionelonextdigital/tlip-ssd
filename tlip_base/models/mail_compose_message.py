from odoo import _, api, fields, models, SUPERUSER_ID

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'
    
    def action_send_mail(self):
        if self.env.user.partner_id in self.partner_ids:
            self = self.with_user(SUPERUSER_ID)
        return super().action_send_mail()
