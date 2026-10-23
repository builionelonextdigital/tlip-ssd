from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OOSMappingCategory(models.Model):
    _name = 'oos.mapping.category'
    _description = 'OOS Mapping Category'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer()
    parent_id = fields.Many2one(
        "oos.mapping.category",
        string="Parent Category",
        ondelete='cascade'
    )
    child_ids = fields.One2many(
        "oos.mapping.category",
        "parent_id",
        copy=False
    )
