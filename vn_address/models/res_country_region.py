from odoo import fields, models


class ResCountryRegion(models.Model):
    _description = 'Region'
    _name = 'res.country.region'
    _order = 'name'

    state_ids = fields.One2many(
        'res.country.state', 'region_id', string='States')
    country_id = fields.Many2one(
        'res.country', required=True, string='Country')
    active = fields.Boolean(default=True)
    name = fields.Char(string='Region Name', required=True)
    code = fields.Char(string='Region Code', required=True)
