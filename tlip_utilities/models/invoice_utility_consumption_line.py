from odoo import api, fields, models, _

class InvoiceUtilityConsumptionLine(models.Model):
    _name = 'invoice.utility.consumption.line'
    _description = 'Invoice Utility Consumption Line'

    move_id = fields.Many2one('account.move', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product', required=True, ondelete='cascade')
    currency_id = fields.Many2one(
        'res.currency', related='move_id.company_currency_id', store=True)
    quantity = fields.Integer('Quantity', required=True)
    unit_price = fields.Monetary(
        string='Unit Price', currency_field='currency_id')
    amount = fields.Monetary(
        string='Amount', currency_field='currency_id',
        compute='_compute_amount', store=True)

    @api.depends('move_id', 'product_id')
    def _compute_display_name(self):
        for r in self:
            text = r.name or r.description
            r.display_name = f'{r.code} {text}' if text else r.code

    @api.depends('unit_price', 'quantity')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.unit_price * rec.quantity
