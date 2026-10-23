from odoo import api, fields, models, _


class ResPartnerCr(models.Model):
    _inherit = "res.partner.cr"

    def _action_effective(self):
        super()._action_effective()
        if self.vendor_code:
            self._notify_purchase_agreement_users()

    def _notify_purchase_agreement_users(self):
        activity_vals = []
        activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
        res_model_id = self.env.ref(
            "purchase_requisition.model_purchase_requisition").id
        purchase_requisitions = self.env["purchase.requisition"].search([
            ("vendor_id", "in", self.reference_partner_id.ids), ("state", "in", ("draft", "confirmed"))])
        for requisition in purchase_requisitions:
            activity_vals.append({
                'activity_type_id': activity_type_id,
                'user_id': requisition.user_id.id,
                'res_id': requisition.id,
                'res_model_id': res_model_id,
                'summary': "Update vendor information"
            })

        self.env["mail.activity"].create(activity_vals)
