from odoo import models, fields, _


class LandPlotGroup(models.Model):
    _name = 'land.plot.group'
    _description = 'Land Plot Group'

    name = fields.Char(required=True)
