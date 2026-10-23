from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    district_id = fields.Many2one(
        'res.country.district', string='District')
    district_name = fields.Char(related='district_id.name')
    district_code = fields.Char(related='district_id.code')
    ward_id = fields.Many2one(
        'res.country.ward', string='Ward')
    ward_name = fields.Char(related='ward_id.name')
    ward_code = fields.Char(related='ward_id.code')
