from odoo import fields, models


class TaskRFQConfirmWizard(models.TransientModel):
    _name = 'task.rfq.confirm.wizard'
    _description = 'Confirm Procurement Task RFQ'

    rfq_selection_id = fields.Many2one(
        comodel_name="task.order.selection", required=True,
        string="RFQ Selection"
    )
    reason = fields.Text()
    bypass_contract = fields.Boolean(
        help="Untick this field will not generate purchase contract and proceed to approval submission")

    def button_confirm(self):
        self.ensure_one()
        rfq_selection = self.rfq_selection_id
        rfq_selection.update_confirm_wizard_vals(
            self._prepare_confirm_wizard_vals())
        return rfq_selection.action_confirm_preference_check()

    def _prepare_confirm_wizard_vals(self):
        self.ensure_one()
        return {"reason": self.reason, "bypass_contract": self.bypass_contract}
