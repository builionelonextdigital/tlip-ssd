from odoo import models, fields, _


class DevelopmentPhase(models.Model):
    _name = 'development.phase'
    _description = 'Development Phase'

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
