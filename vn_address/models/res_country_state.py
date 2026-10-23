from unidecode import unidecode

from odoo import api, fields, models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    district_ids = fields.One2many(
        'res.country.district', 'country_state_id', string='Districts')
    region_id = fields.Many2one(
        'res.country.region', string="Region")
    
    plain_name = fields.Char(compute='_compute_plain_name', store=True)

    @api.depends('name')
    def _compute_plain_name(self):
        for record in self:
            record.plain_name = unidecode(record.name) if record.name else False
