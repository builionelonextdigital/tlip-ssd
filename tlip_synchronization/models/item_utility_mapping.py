from odoo import fields, models


class ItemUtilityMapping(models.Model):
    _name = "item.utility.mapping"
    
    product_id = fields.Many2one('product.product', string='Goods/Service', required=True)
    item_code = fields.Char(string='Mapping Item Code', required=True)
    utility_type = fields.Selection([('electricity', 'Electricity'),
                                     ('water', 'Water')], required=True)

    company_id = fields.Many2one('res.company')
