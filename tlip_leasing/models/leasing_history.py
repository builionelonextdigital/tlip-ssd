from odoo import models, fields

class LeaseHistory(models.Model):
    _name = 'leasing.history'
    _description = 'Leasing History'

    land_plot_id = fields.Many2one('stock.location', required=True)
    agreement_id = fields.Many2one('leasing.agreement', required=True, string="Contract")
    lessee_id = fields.Many2one('res.partner', 'Customer')
    lease_period = fields.Char('Lease Period')
    price_unit = fields.Float('Unit Price')