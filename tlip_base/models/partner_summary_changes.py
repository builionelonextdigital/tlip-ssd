from odoo import fields, models, _

class PartnerSummaryChanges(models.Model):
    _name = 'partner.summary.change'
    _description = 'Partner Summary Changes'

    name = fields.Char(string="Field")
    current_value = fields.Text(string="Current")
    new_value = fields.Text(string="New")
    partner_cr_id = fields.Many2one('res.partner.cr', ondelete='cascade')
