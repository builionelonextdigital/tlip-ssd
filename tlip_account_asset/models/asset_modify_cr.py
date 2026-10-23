from odoo import _, models, fields, api
from odoo.exceptions import UserError

from contextlib import closing


CR_TYPE_FUNC_CONFIRM_MAPPING = {
    "pause": "pause",
    "modify": "modify",
    "resume": "modify",
    "sell": "sell_dispose",
    "dispose": "sell_dispose"
}


class AssetModifyCR(models.Model):
    _name = 'asset.modify.cr'
    _inherit = ['asset.modify', 'approval.matrix.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Asset Modify Information'
    _rec_name = 'cr_name'

    cr_name = fields.Char(string='Name', required=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("wait_for_approval", "Waiting for Approval"),
        ("approved", "Approved"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
        ("cancel", "Cancelled"),
    ], string='Approval State', default='draft', tracking=True)
    approval_readonly = fields.Boolean(compute="_compute_approval_readonly")

    def _compute_approval_readonly(self):
        for rec in self:
            approval_readonly = rec.state != 'draft'
            rec.approval_readonly = approval_readonly

    def open_asset_view(self):
        return self.asset_id.open_asset(['form'])

    def action_reset_approval(self):
        "Approval State: Rejected | Withdrawn -> Draft"
        self.write({"state": "draft"})

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action["context"]["default_name"] = _(
            f"Approval Request for Asset Modify {self.cr_name}"
        )
        return action

    def action_cancel(self):
        self.write({"state": "cancel"})

    def modify(self):
        res = super().modify()
        self.write({'state': 'completed'})
        return res
    
    def pause(self):
        res = super().pause()
        self.write({'state': 'completed'})
        return res

    def sell_dispose(self):
        res = super().sell_dispose()
        self.write({'state': 'completed'})
        return res

    def _trigger_action_approve(self):
        self.write({"state": "approved"})

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({'state': 'wait_for_approval'})
        return result

    def _trigger_action_withdraw(self, reason: str):
        self.action_cancel()
        super()._trigger_action_withdraw(reason)

    def _validate_submit_approval(self):
        # Will roll back the created record if the method pass validation
        with closing(self.env.cr.savepoint()):
            for rec in self:
                if rec.state != "draft":
                    raise UserError(_("Only draft CR can be submitted."))
                
                # To call the asset modify method for data validation before submit approval
                method = CR_TYPE_FUNC_CONFIRM_MAPPING.get(rec.modify_action)
                if method:
                    if rec.modify_action == 'modify':
                        rec = rec.with_context(tlip_custom_asset=True)
                    getattr(rec, method)()

            self.pool.clear_all_caches()
            # don't propagate to other workers since it was rollbacked
            self.pool.reset_changes()
