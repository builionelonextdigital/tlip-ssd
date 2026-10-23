from odoo import api, fields, models, _


class InvoiceType(models.Model):
    _inherit = 'invoice.type'

    utility_electricity_type = fields.Selection(selection=[
        ('consumption', 'Consumption'),
        ('reactive_power', 'Reactive Power'),
        ('connection_charge', 'Connection Charge')
    ])
