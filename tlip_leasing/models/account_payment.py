from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    deposit_invoice_id = fields.Many2one(
        'account.move',
        string='Deposit Invoice',
        domain=[('move_type', '=', 'out_invoice')],
        help='The invoice for which this payment is a deposit'
    )