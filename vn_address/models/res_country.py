from odoo import api, fields, models


class ResCountry(models.Model):
    _inherit = 'res.country'

    region_ids = fields.One2many(
        'res.country.region', 'country_id', string='Regions')
