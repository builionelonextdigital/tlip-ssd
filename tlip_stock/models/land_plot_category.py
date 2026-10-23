from odoo import models, fields, _


class LandPlotCategory(models.Model):
    _name = 'land.plot.category'
    _description = 'Land Plot Category'
    _parent_name = "parent_id"
    _parent_store = True

    name = fields.Char(required=True)
    parent_id = fields.Many2one('land.plot.category', 'Parent Category', index=True)
    parent_path = fields.Char(index=True)
