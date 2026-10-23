from odoo import fields, models, _

class LeasingSummaryChanges(models.Model):
    _name = 'leasing.summary.changes'
    _description = 'Leasing Summary Changes'

    name = fields.Char(string="Field")
    current_value = fields.Text(string="Current")
    new_value = fields.Text(string="New")
    supplement_agreement_id = fields.Many2one('leasing.supplement', ondelete='cascade')