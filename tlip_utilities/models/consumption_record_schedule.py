import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.tools.date_utils import start_of, end_of

_logger = logging.getLogger(__name__)


class ConsumptionRecordSchedule(models.Model):
    _name = 'consumption.record.schedule'

    day_in_month = fields.Selection([('6', '6'),
                                     ('7', '7'),
                                     ('10', '10'),
                                     ('13', '13'),
                                     ('15', '15'),
                                     ('17', '17'),
                                     ('18', '18'),
                                     ('20', '20'),
                                     ('25', '25'),
                                     ('28', '28'),
                                     ('end_month', 'End of Month')])

    electricity_point_id = fields.Many2one(
        'electricity.point', 'Electricity Point', ondelete='cascade')
    water_point_id = fields.Many2one(
        'water.point', 'Electricity Point', ondelete='cascade')
    electricity_consumption_id = fields.Many2one(
        'electricity.consumption', string='Consumption Record')
    water_consumption_id = fields.Many2one(
        'water.consumption', string='Consumption Record')

    def _compute_electricity_consumption_id(self):
        current_period = self.env['accounting.period.closing']._get_current_accounting_period(
        )
        start_period, end_period = start_of(current_period.accounting_period, 'month'), end_of(
            current_period.accounting_period, 'month')

        point_groups = self.env["electricity.consumption"].read_group(
            [
                (
                    "electricity_point_id",
                    "in",
                    self.mapped('electricity_point_id').ids,
                ),
                ('date_from', '>=', start_period),
                ('date_to', '<=', end_period)
            ],
            ["electricity_point_id", "date_to", "ids:array_agg(id)"],
            ["electricity_point_id", "date_to:day"],
            lazy=False
        )
        
        ids_per_date_point = {
            (group["electricity_point_id"], datetime.strptime(group['date_to:day'], "%d %b %Y").date()): group["ids"] for group in point_groups
        }

        for record in self:
            if record.day_in_month != 'end_month':
                day_in_month = int(record.day_in_month)
                record_date = start_period.replace(day_in_month)
            else:
                record_date = end_period 
            consumption_ids = ids_per_date_point.get(
                (record.electricity_point_id, record_date), [])
            if consumption_ids:
                record.electricity_consumption_id = consumption_ids[-1]
            else:
                record.electricity_consumption_id = False

    def _compute_water_consumption_id(self):
        current_period = self.env['accounting.period.closing']._get_current_accounting_period(
        )
        start_period, end_period = start_of(current_period.accounting_period, 'month'), end_of(
            current_period.accounting_period, 'month')
        point_groups = self.env["water.consumption"].read_group(
            [
                (
                    "water_point_id",
                    "in",
                    self.mapped('water_point_id').ids,
                ),
                ('date_from', '>=', start_period),
                ('date_to', '<=', end_period)
            ],
            ["water_point_id", "date_to", "ids:array_agg(id)"],
            ["water_point_id", "date_to:day"],
            lazy=False
        )

        ids_per_date_point = {
            (group["water_point_id"], datetime.strptime(group['date_to:day'], "%d %b %Y").date()): group["ids"] for group in point_groups
        }

        for record in self:
            if record.day_in_month != 'end_month':
                day_in_month = int(record.day_in_month)
                record_date = start_period.replace(day_in_month)
            else:
                record_date = end_period 
            consumption_ids = ids_per_date_point.get(
                (record.water_point_id, record_date), [])
            if consumption_ids:
                record.water_consumption_id = consumption_ids[-1]
            else:
                record.water_consumption_id = False
