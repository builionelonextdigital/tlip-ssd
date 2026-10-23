from odoo import models, fields, api

class PaymentContactLine(models.Model):
    _name = 'payment.contact.line'
    _description = 'Payment Contact Line'

    partner_id = fields.Many2one('res.partner', ondelete='cascade', required=True)
    invoice_type_id = fields.Many2one('invoice.type', ondelete='cascade', required=True)
    contact_ids = fields.Many2many('res.partner', domain="[('parent_id', '=', partner_id)]")
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    direct_debit = fields.Boolean(string='Debit Direct', default=False, copy=False)
    payment_contact_line_ids = fields.One2many('payment.contact.line', 'partner_id', string='Payment Contacts')
