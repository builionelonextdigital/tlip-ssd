from odoo import models, api, _

class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, values_list):
        mails = super().create(values_list)
        for mail in mails:
            email_address = mail.mail_server_id.smtp_user or self.env['ir.mail_server']._get_default_from_address()
            if mail.author_id:
                vals = {
                    'email_from': f"\"{mail.author_id.name}\" <{email_address}>" if email_address else mail.email_from,
                }
                mail.update(vals)
        return mails
