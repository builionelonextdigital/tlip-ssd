from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetRevaluationReason(models.Model):
    _name = 'asset.revaluation.reason'
    _description = 'Asset Revaluation Reason'

    name = fields.Char(required=True)
    type = fields.Selection([
        ('increase', 'Increase'),
        ('decrease', 'Decrease')
    ], required=True)
