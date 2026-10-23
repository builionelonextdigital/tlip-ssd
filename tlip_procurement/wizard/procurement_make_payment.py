from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError

class ProcurementMakePayment(models.TransientModel):
    _name = 'procurement.make.payment'
    _description = 'Procurement Make Payment'

    purchase_order_id = fields.Many2one('purchase.order')
    currency_id = fields.Many2one(related='purchase_order_id.currency_id')
    type = fields.Selection([('advance_payment', 'Advance Payment'),
                             ('bill_payment', 'Bill Payment')], required=True)
    bill_ids = fields.Many2many('account.move', string='Bills')
    available_bill_ids = fields.Many2many('account.move', 'procurement_bill_ref', 'move_id', 'wizard_id')

    def _prepare_account_payment_vals(self):
        self.ensure_one()
        move_lines = self.mapped('bill_ids.line_ids').filtered(lambda l: l.account_id.account_type == 'liability_payable')
        vals = {
            'partner_id': self.purchase_order_id.partner_id.id,
            'payment_type': 'outbound',
            'currency_id': self.currency_id.id,
            'is_request_payment': True,
            'is_advance_payment': self.type == 'advance_payment',
            'partner_type': 'supplier',
            'development_project_id': self.purchase_order_id.development_project_id.id,
            'development_phase_id': self.purchase_order_id.development_phase_id.id,
            'purchase_order_id': self.purchase_order_id.id,
            'amount': self.purchase_order_id.amount_residual,
            'auto_reconcile_item_ids': [(6, 0, move_lines.ids)]
        }
        return vals

    def action_confirm(self):
        self.ensure_one()

        if self.type == 'advance_payment' and not self.purchase_order_id.is_advance_enabled:
            raise ValidationError(_('You cannot make advance payment'))

        payment = self.env['account.payment'].create(
            self._prepare_account_payment_vals())
        action = self.env['ir.actions.actions']._for_xml_id(
            'tlip_account.action_outbound_payment_request_payment')
        action.update({
            'target': 'current',
            'res_id': payment.id,
            'views': [(self.env.ref('tlip_account.view_payment_request_payment_form').id, 'form')],
        })
        return action
