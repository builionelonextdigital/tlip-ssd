from odoo import fields, models, _

class PurchaseSummaryChanges(models.Model):
    _name = 'purchase.summary.change'
    _description = 'Purchase Summary Changes'

    name = fields.Char(string="Field")
    current_value = fields.Text(string="Current")
    new_value = fields.Text(string="New")
    purchase_supplement_id = fields.Many2one('purchase.supplement', ondelete='cascade')
