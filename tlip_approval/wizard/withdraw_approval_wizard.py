from odoo import models, fields


class WithdrawApprovalWizard(models.TransientModel):
    _name = "withdraw.approval.wizard"
    _description = "Withdraw Approval Wizard"

    related_model = fields.Char(string='Related Model', required=True)
    related_res_id = fields.Many2oneReference(string='Related Document ID', model_field='related_model', required=True)
    reason = fields.Text(required=True)

    def action_confirm(self):
        # trigger action withdraw mixin
        self.env[self.related_model].browse(
            self.related_res_id)._trigger_action_withdraw(self.reason)
