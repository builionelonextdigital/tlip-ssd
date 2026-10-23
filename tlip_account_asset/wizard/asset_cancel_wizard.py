from odoo import models, fields

class AssetCancelWizard(models.TransientModel):
    _name = 'asset.cancel.wizard'
    _description = 'Asset Cancel Wizard'

    reason = fields.Text(string='Reason for Cancellation', required=True)

    def action_cancel_asset(self):
        self.ensure_one()
        asset = self.env['account.asset'].browse(self._context.get('active_id'))
        asset.with_context(cancel_reason=self.reason).set_to_cancelled()