from odoo import models, _


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        """ Override of ``mail.thread`` method to prevent approvers from being unsubscribed from the thread.
        This is needed as approvers are automatically subscribed to the thread and we don't want the system
        to subscribe them"""
        if self.env.context.get('skip_approver_subscribe', False):
            partner_ids = []
        return super(MailThread, self)._message_subscribe(partner_ids=partner_ids, subtype_ids=subtype_ids, customer_ids=customer_ids)
