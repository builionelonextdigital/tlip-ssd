from odoo import models, fields, _


class ProductManufacturer(models.Model):
    _name = 'product.manufacturer'
    _description = 'Product Manufacturer'

    name = fields.Char(required=True)