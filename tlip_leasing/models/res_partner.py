from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_change_requests_customer(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.tlip_leasing_customer_cr_action')
        action['domain'] = [("reference_partner_id", "=", self.id)]
        context = eval(action.get('context', {}))
        context.update({
            'default_cr_type': 'customer'
        })
        return action

    def action_update_contact_info(self):
        result = super().action_update_contact_info()
        if self._context.get('leasing_customer'):
            return self.action_view_change_requests_customer()
        return result
