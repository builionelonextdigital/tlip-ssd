from odoo import fields, models

class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'
    
    company_id = fields.Many2one('res.company')
