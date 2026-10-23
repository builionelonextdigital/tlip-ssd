from odoo import models, fields, api, _


class UtilitiesPricelistItem(models.Model):
    _name = 'utilities.pricelist.item'
    _description = 'Utilities Pricelist Item'

    product_id = fields.Many2one(
        'product.product', 'Apply On',
        required=True)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id',
                             string='UoM', store=True)
    pricelist_id = fields.Many2one('utilities.pricelist', required=True)
    currency_id = fields.Many2one(related='pricelist_id.currency_id')
    unit_price = fields.Float('Unit Price')
    budget_code_id = fields.Many2one('budget.code', string='Budget Code', required=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.unit_price = self.product_id.list_price
        self.budget_code_id = self.product_id.income_budget_code_id
