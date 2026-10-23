from odoo import api, fields, models


class SignTicketSigner(models.Model):
    _name = "sign.ticket.signer"
    _description = "Sign Ticket Signer"
    _order = "sequence, id"

    ticket_id = fields.Many2one(
        comodel_name="sign.ticket",
        string="Ticket",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    line_number = fields.Integer(
        string="Signer Number",
        compute="_compute_line_number",
        store=False
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
    )
    state = fields.Selection(
        selection=[
            ("waiting", "Waiting"),
            ("signed", "Signed"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        required=True,
        default="waiting",
    )
    is_allow_to_approve_reject = fields.Boolean(
        compute="_compute_is_allow_to_approve_reject",
        string="Can Approve/Reject",
    )
    reject_reason = fields.Text(string="Rejection Reason")

    @api.depends('ticket_id', 'ticket_id.signer_line_ids')
    def _compute_line_number(self):
        for record in self:
            ticket_signers = record.ticket_id.signer_line_ids
            record.line_number = ticket_signers._origin.ids.index(record._origin.id) + 1 if record._origin.id else 1

    @api.model
    def _get_waiting_state(self):
        return "waiting"

    def _reset_status(self):
        self.write({"state": "waiting"})

    def action_sign(self):
        self.write({"state": "signed"})

    @api.depends("user_id", "state", "ticket_id.state")
    def _compute_is_allow_to_approve_reject(self):
        for record in self:
            record.is_allow_to_approve_reject = (
                record.user_id == self.env.user
                and record.state in record._get_waiting_state()
                and record.ticket_id.state == "in_progress"
            )
