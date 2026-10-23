from odoo import models


class SignTicketRejectWizard(models.TransientModel):
    _inherit = "sign.ticket.reject.wizard"

    def action_confirm_reject(self):
        res = super().action_confirm_reject()
        ticket = self.ticket_id
        ticket.action_reject_request()

        return res
