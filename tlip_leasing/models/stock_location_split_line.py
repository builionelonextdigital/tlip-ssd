from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LandPlotSplitLine(models.Model):
    _name = 'stock.location.split.line'
    _description = 'Land Plot Split Line'

    cr_id = fields.Many2one(
        comodel_name="stock.location.cr",
        required=True,
        ondelete="cascade"
    )
    name = fields.Char(string="New Land Plot", required=True)
    gross_area = fields.Float()
    saleable_area = fields.Float()
    land_plot_category_id = fields.Many2one(
        string="Category",
        comodel_name='land.plot.category',
    )
    date_start = fields.Date('Effective From', required=True)
    date_end = fields.Date('Effective To', required=True)

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        # Note: update condition in create function
        for record in self:
            if record.date_start and record.date_end and record.date_start > record.date_end:
                raise ValidationError(_(f"Land Plot {record.name} - Start date should precede the end date."))

    @api.constrains("gross_area", "saleable_area")
    def _check_area(self):
        # Note: update condition in create function
        for record in self:
            if record.gross_area < record.saleable_area:
                raise ValidationError(_(f"Land Plot {record.name} - Saleable area should not be larger than gross area."))

    def _prepare_new_info_land_plot(self, vals={}):
        self.ensure_one()
        land_plot_vals = {
            'name': self.name,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'gross_area': self.gross_area,
            'saleable_area': self.saleable_area,
            'land_plot_category_id' :self.land_plot_category_id.id
        }
        if vals:
            land_plot_vals.update(vals)
        return land_plot_vals

    @api.model
    def check_constrains_upon_create(self, vals_list):
        for *others, vals in vals_list:
            name = vals.get('name')
            date_start = vals.get('date_start')
            date_end = vals.get('date_end')
            if date_start and date_end and date_start > date_end:
                raise ValidationError(_(f"Land Plot {name} - Start date should precede the end date."))

            gross_area = vals.get('gross_area')
            saleable_area = vals.get('saleable_area')
            if gross_area < saleable_area:
                raise ValidationError(_(f"Land Plot {name} - Saleable area should not be larger than gross area."))
