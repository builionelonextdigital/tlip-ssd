from calendar import monthrange

from odoo import fields, models

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _create_date_range_seq(self, date):
        if not self.env.context.get('month_sequence', {}):
            return super()._create_date_range_seq(date)
        else:
            date_format = fields.Date.from_string(date)
            month_year = date_format.strftime('%Y-%m')
            date_from = '{}-01'.format(month_year)
            date_to = '%s-%s' % (month_year, monthrange(date_format.year, date_format.month)[1])
            seq_date_range = self.env['ir.sequence.date_range'].sudo().create({
                'date_from': date_from,
                'date_to': date_to,
                'sequence_id': self.id,
            })
            return seq_date_range
