from odoo import _, fields, models


class SignTicketRejectWizard(models.TransientModel):
    _name = "sign.ticket.reject.wizard"
    _description = "Sign Ticket Reject Wizard"

    ticket_id = fields.Many2one(
        comodel_name="sign.ticket",
        string="Ticket",
        required=True,
    )
    signer_id = fields.Many2one(
        comodel_name="sign.ticket.signer",
        string="Signer",
        required=True,
    )
    reason = fields.Text(string="Rejection Reason")

    def action_confirm_reject(self):
        self.ensure_one()
        self.ticket_id.write({"state": "rejected"})
        self.signer_id.write({
            "state": "rejected",
            "reject_reason": self.reason,
        })
        if self.reason:
            self.ticket_id.message_post(
                body=_("Ticket rejected. Reason: %s") % self.reason
            )
        return {"type": "ir.actions.act_window_close"}
