from unidecode import unidecode

from odoo import api, fields, models


class Ward(models.Model):
    _description = 'Ward'
    _name = 'res.country.ward'
    _order = 'code'

    district_id = fields.Many2one(
        'res.country.district', string='District', required=True)
    active = fields.Boolean(default=True)
    name = fields.Char(string='Ward Name', required=True)
    code = fields.Char(string='Ward Code', required=True)

    plain_name = fields.Char(compute='_compute_plain_name', store=True)

    @api.depends('name')
    def _compute_plain_name(self):
        for record in self:
            record.plain_name = unidecode(record.name) if record.name else False