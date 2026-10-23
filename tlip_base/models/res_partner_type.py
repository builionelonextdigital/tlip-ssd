from odoo import fields, models, _


class PartnerType(models.Model):
    _name = 'res.partner.type'
    _description = 'Partner Type'

    name = fields.Char(required=True)
