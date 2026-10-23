from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    consumption_from = fields.Float(
        string="Consumption From"
    )
    consumption_to = fields.Float(
        string="Consumption To"
    )
    electricity_payment_due_date = fields.Integer(
        string="Electricity Payment Due Date"
    )
    water_payment_due_date = fields.Integer(
        string="Water Payment Due Date"
    )
    
    electrict_journal_id = fields.Many2one('account.journal')
    water_journal_id = fields.Many2one('account.journal')
    reactive_power_product_id = fields.Many2one('product.product')
    power_connection_product_id = fields.Many2one('product.product')

    electrict_consumption_invoice_type_id = fields.Many2one('invoice.type')
    electrict_reactive_power_invoice_type_id = fields.Many2one('invoice.type')
    water_consumption_invoice_type_id = fields.Many2one('invoice.type')
    electrict_connection_invoice_type_id = fields.Many2one('invoice.type')
    water_connection_invoice_type_id = fields.Many2one('invoice.type')
    
    
