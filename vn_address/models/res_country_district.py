from unidecode import unidecode
from odoo import api, fields, models


class District(models.Model):
    _description = 'District'
    _name = 'res.country.district'
    _order = 'code'

    country_state_id = fields.Many2one(
        'res.country.state', string='Province', required=True)
    active = fields.Boolean(default=True)
    name = fields.Char(string='District Name', required=True)
    code = fields.Char(string='District Code', required=True)
    ward_ids = fields.One2many(
        'res.country.ward', 'district_id', string='Wards')
    plain_name = fields.Char(compute='_compute_plain_name', store=True)

    @api.depends('name')
    def _compute_plain_name(self):
        for record in self:
            record.plain_name = unidecode(record.name) if record.name else False