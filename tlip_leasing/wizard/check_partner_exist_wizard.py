from odoo import models, fields


class CheckPartnerExistWizard(models.TransientModel):
    _inherit = 'check.partner.exist.wizard'

    def button_check_exist(self):
        partner = super().button_check_exist()
        if self.check_type == 'customer':
            action = self.env["ir.actions.actions"]._for_xml_id(
                "tlip_leasing.tlip_leasing_customer_registration_action")
            if partner:
                context = eval(action.get('context', {}))
                context.update({'partner_readonly': True})
                action["res_id"] = partner.id
                action["context"] = context
            action.update({
                "views": [[self.env.ref('tlip_leasing.view_tlip_leasing_customer_form').id, 'form']]
            })
            return action
        return partner
