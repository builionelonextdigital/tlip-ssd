from odoo import models, fields, api, _, Command


class ProcurementSelectRequestType(models.TransientModel):
    _name = 'procurement.select.request.type'

    def _default_request_type(self):
        return "advance_payment" if self.env.context.get('is_advance_enabled') else "bill_payment"

    request_id = fields.Many2one('request.purchase', string='Request', required=True)
    request_type = fields.Char(required=True, default=_default_request_type, string='Request Type')

    def prepare_account_payment_values(self):
        self.ensure_one()
        request = self.request_id
        vendor = self.request_id.user_id.partner_id
        if self.request_type == 'bill_payment':
            vendor = self.request_id.vendor_id

        return {
            'payment_type': 'outbound',
            'partner_id': vendor.id,
            'amount': request.amount_total,
            'request_purchase_id': request.id,
            'is_request_payment': True,
            'partner_type': 'supplier',
            'destination_account_id': vendor.with_company(request.company_id).property_account_payable_id.id,
            'is_advance_payment': self.request_type == 'advance_payment',
            'currency_id': request.currency_id.id,
            'company_id': request.company_id.id,
        }


    def _generate_payment(self):
        self.ensure_one()
        payment = self.env['account.payment'].create(
            self.prepare_account_payment_values()
        )
        action = self.env['ir.actions.actions']._for_xml_id('account.action_account_payments_payable')
        action.update({
            'name': _('Request for Payment'),
            'views': [(self.env.ref('tlip_account.view_payment_request_payment_form').id, 'form')],
            'target': 'current',
            'res_id': payment.id,
            'context': {
                'create': False,
            }
        })
        return action

    def action_confirm(self):
        self.ensure_one()
        result = self._generate_payment()
        return result
    
    @api.model
    def get_request_type_selection(self):
        request_type_list = []
        if self.env.context.get("is_advance_enabled"):
            request_type_list.append(('advance_payment', 'Advance Payment'))

        request_type_list.append(('bill_payment', 'Bill Payment'))
        return request_type_list
