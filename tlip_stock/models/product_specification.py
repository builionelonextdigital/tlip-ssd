from odoo import models, fields, _


class ProductManufacturer(models.Model):
    _name = 'product.specification'
    _description = 'Product Manufacturer'

    name = fields.Char('Fields', required=True)
    value = fields.Char('Value', required=True)
    product_template_id = fields.Many2one('product.template', string='Product Template', required=True, ondelete='cascade')