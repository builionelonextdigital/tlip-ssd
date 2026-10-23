from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    consumption_from = fields.Float(
        string="Consumption From",
        readonly=False,
        related="company_id.consumption_from",
    )
    consumption_to = fields.Float(
        string="Consumption To",
        readonly=False,
        related="company_id.consumption_to",
    )
    electricity_payment_due_date = fields.Integer(
        string="Electricity Payment Due Date",
        readonly=False,
        related="company_id.electricity_payment_due_date",
    )
    water_payment_due_date = fields.Integer(
        string="Water Payment Due Date",
        readonly=False,
        related="company_id.water_payment_due_date",
    )
    electrict_journal_id = fields.Many2one('account.journal', related='company_id.electrict_journal_id', readonly=False, required=True)
    water_journal_id = fields.Many2one('account.journal', related='company_id.water_journal_id', readonly=False, required=True)
    reactive_power_product_id = fields.Many2one('product.product', related='company_id.reactive_power_product_id', readonly=False, required=True)
    power_connection_product_id = fields.Many2one('product.product', related='company_id.power_connection_product_id', readonly=False, required=True)

    electrict_consumption_invoice_type_id = fields.Many2one('invoice.type', related='company_id.electrict_consumption_invoice_type_id', readonly=False, required=True)
    electrict_reactive_power_invoice_type_id = fields.Many2one('invoice.type', related='company_id.electrict_reactive_power_invoice_type_id', readonly=False, required=True)
    electrict_connection_invoice_type_id = fields.Many2one('invoice.type', related='company_id.electrict_connection_invoice_type_id', readonly=False, required=True)

    water_consumption_invoice_type_id = fields.Many2one('invoice.type', related='company_id.water_consumption_invoice_type_id', readonly=False, required=True)
    water_connection_invoice_type_id = fields.Many2one('invoice.type', related='company_id.electrict_connection_invoice_type_id', readonly=False, required=True)