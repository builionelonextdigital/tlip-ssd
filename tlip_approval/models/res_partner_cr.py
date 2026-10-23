from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerCr(models.Model):
    _name = "res.partner.cr"
    _inherit = ["res.partner.cr", "approval.matrix.mixin"]

    def action_submit_approval(self):
        if self.filtered(lambda r: r.state != 'draft'):
            raise UserError(
                _('You cannot submit a Change Request that is not in Draft state.'))
        action = super().action_submit_approval()
        action['context']['default_name'] = _(
            f'Approval Partner Change Request {self.complete_name}')
        return action

    def action_submit_changes(self):
        self.ensure_one()
        if not (self.effective_date and self.reason):
            raise UserError(
                _('Please select an effective date and provide a reason for the change.'))

        summary_change_vals = self._get_difference_record_changes(
            self.reference_partner_id)
        if not summary_change_vals:
            raise ValidationError(
                _('There are no changes found. Please check and try again.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _("Summary of changes"),
            'res_model': 'partner.summary.change.wizard',
            'views': [(self.env.ref('tlip_base.partner_summary_change_wizard_view_form').id, 'form')],
            'target': 'new',
            'context': {
                'default_partner_cr_id': self.id,
                'default_change_line_ids': summary_change_vals,
            }
        }

    def _trigger_action_withdraw(self, reason: str):
        res = super()._trigger_action_withdraw(reason)
        self.action_cancel()
        return res

    def _trigger_action_approve(self):
        today = fields.Date.today()
        self.write({
            'state': 'approved',
            'date_approved': today
        })
        for record in self.filtered(lambda r: r.effective_date <= today):
            record._action_effective()

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'to_approve',
        })
        return result
