from odoo import api, fields, models


class SignTicketSigner(models.Model):
    _inherit = 'sign.ticket.signer'

    approver_id = fields.Many2one(
        comodel_name='approval.approver',
        string='Approver',
        ondelete='set null',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        compute='_compute_user_id',
        store=True,
        required=False,
        readonly=True,
    )
    job_id = fields.Many2one(
        comodel_name='hr.job',
        related='approver_id.job_id',
        store=False,
        required=False,
        readonly=True,
    )

    @api.depends('approver_id.user_id')
    def _compute_user_id(self):
        for rec in self:
            rec.user_id = rec.approver_id.user_id

    def _mysign_postprocess(self, signed_bytes_list, api_docs):
        super()._mysign_postprocess(signed_bytes_list, api_docs)
        for ticket in self.mapped('ticket_id'):
            ticket.action_approve_request()

    def _build_api_doc(self, doc, target_word):
        res = super()._build_api_doc(doc, target_word)
        
        employee_id = self.approver_id._get_employee() or self.env['hr.employee']
        res.update({
            "signer_name": self.env.user.name,
            "stamp_img": employee_id.e_signature_file,
        })
        return res

    def _log_mysign_error(self, error: str):
        self.ensure_one()
        super()._log_mysign_error(error)
        self.write({"user_id": False})
