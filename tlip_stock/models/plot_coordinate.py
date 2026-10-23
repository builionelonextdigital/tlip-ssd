from odoo import models, fields


class PlotCoordinate(models.Model):
    _name = 'plot.coordinate'
    _description = 'Plot Coordinate'

    land_plot_id = fields.Many2one('stock.location', required=True)
    name = fields.Char('Point')
    value = fields.Char('Value')