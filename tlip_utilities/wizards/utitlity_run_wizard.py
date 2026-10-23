from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class UtilityRunWizard(models.TransientModel):
    _name = 'utility.run.wizard'
    
    date_from = fields.Date(string='Record Date From', required=True)
    date_to = fields.Date(string='Record Date To', required=True)
    utility_type = fields.Selection([('electric', 'Electric'), ('water', 'Water')], required=True)
    electricity_point_id = fields.Many2one('electricity.point')
    water_point_id = fields.Many2one('water.point')
    
    @api.onchange('utility_type')
    def _onchange_utility_type(self):
        if self.utility_type != 'electric':
            self.electricity_point_id = False
        else:
            self.water_point_id = False

    def run(self):
        self.ensure_one()
        date_from = fields.Datetime.to_datetime(self.date_from).replace(hour=0, minute=0, second=0)
        date_to = fields.Datetime.to_datetime(self.date_to).replace(hour=23, minute=59, second=59)
        
        if self.utility_type == 'electric' and not self.env.user.has_groups('tlip_utilities.group_electricity_user'):
            raise ValidationError(_('You do not have permission to do this operation'))
        
        if self.utility_type == 'water' and not self.env.user.has_groups('tlip_utilities.group_water_user'):
            raise ValidationError(_('You do not have permission to do this operation'))

        if self.electricity_point_id or self.water_point_id:
            point = self.electricity_point_id or self.water_point_id
            point._run(company=point.company_id, date_from=date_from, date_to=date_to)
        else:
            if self.utility_type == 'electric':
                model = 'electricity.point'
            else:
                model = 'water.point'
            self.env[model]._synchronize_consumption(date_from, date_to)
