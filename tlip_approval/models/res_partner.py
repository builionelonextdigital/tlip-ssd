from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "approval.matrix.mixin"]

    def action_submit_approval(self):
        partner_type = self.env.context.get('approval_partner_type')
        if self.filtered(lambda rec: getattr(rec, f"{partner_type}_state") != 'draft'):
            raise UserError(
                _(f'You cannot submit a {partner_type} that is not in Draft state.'))
        action = super().action_submit_approval()
        action['context'].update({
            'default_name': _(f'Approval {partner_type} {self.complete_name}'),
            'default_identify_key': partner_type
        })
        return action

    def action_reset(self):
        partner_type = self.env.context.get('approval_partner_type')
        self.write({f'{partner_type}_state': 'draft'})

    def _trigger_action_approve(self):
        if self.vendor_state == 'to_approve':
            vendor_code = self._calculate_partner_code("procurement.vendor")
            self.write({
                'vendor_state': 'approved',
                'vendor_registration_date': fields.Date.today(),
                'vendor_code': vendor_code
            })
        if self.customer_state == 'to_approve':
            customer_code = self._calculate_partner_code("leasing.customer")
            self.write({
                'customer_state': 'approved',
                'customer_registration_date': fields.Date.today(),
                'customer_code': customer_code
            })

    def _trigger_action_refuse(self):
        if self.vendor_state == 'to_approve':
            self.write({
                'vendor_state': 'rejected',
            })
        if self.customer_state == 'to_approve':
            self.write({
                'customer_state': 'rejected',
            })

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        partner_type = self.env.context.get('identify_key')
        self.write({
            f'{partner_type}_state': 'to_approve',
        })
        return result

    def _calculate_partner_code(self, sequence_name):
        partner_code = (
            self.env["ir.sequence"]
            .with_context(month_sequence=True)
            .with_company(self.env.company)
            .next_by_code(sequence_name) or "/"
        )
        return partner_code
