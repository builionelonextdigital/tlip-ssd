from odoo import api, fields, models, _


class DevelopmentProject(models.Model):
    _name = "development.project"
    _description = "Development Project"

    name = fields.Char(required=True)
    code = fields.Char(string='Project Code', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)