from odoo import fields, models


class ChecklistTemplate(models.Model):
    _name = 'checklist.template'

    name = fields.Char(string='Name', required=True)
    condition = fields.Char(
        string='Condition', required=True, default='[]',
        help='Condition to be met for this checklist to be applicable'
    )
    description = fields.Html(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='State', default='draft', required=True)

    # Relationship fields
    related_model_id = fields.Many2one(
        'ir.model', string='Model', required=True,
        ondelete='cascade', help='Model to which this checklist is associated'
    )
    related_model_name = fields.Char(related='related_model_id.model', readonly=True)

    # Action methods
    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_reset(self):
        self.write({'state': 'draft'})
