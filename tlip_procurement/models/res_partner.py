from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    request_purchase_quota = fields.Float(
        string="Purchase Quota",
        default=lambda self: self.env.company.employee_purchase_quota,
        help="The maximum amount that can be requested",
    )
    request_purchase_used = fields.Float(
        string="Purchased Amount",
        store=True,
    )

    def action_view_change_requests_vendor(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_procurement.tlip_procurement_vendor_cr_action')
        action['domain'] = [("reference_partner_id", "=", self.id)]
        context = eval(action.get('context', {}))
        context.update({
            'default_cr_type': 'vendor'
        })
        action['context'] = context
        return action

    def action_update_contact_info(self):
        result = super().action_update_contact_info()
        if self._context.get('procurement_vendor'):
            return self.action_view_change_requests_vendor()
        return result
