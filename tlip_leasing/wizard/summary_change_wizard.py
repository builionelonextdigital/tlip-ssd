from odoo import fields, models, Command, _


class SummaryChangeWizard(models.TransientModel):
    _name = "summary.change.wizard"
    _description = "Summary Change Wizard"

    supplement_agreement_id = fields.Many2one('leasing.supplement', required=True)    
    change_line_ids = fields.One2many('summary.change.line', 'wizard_id')
    reason = fields.Text(related='supplement_agreement_id.reason', readonly=True)
    effective_date = fields.Date(related='supplement_agreement_id.effective_date', readonly=True)

    def button_confirm(self):
        changes_to_update = self.change_line_ids.filtered(lambda l: not l.bypass_create)
        if changes_to_update:
            self.supplement_agreement_id.write({
                'summary_change_ids': [Command.create({
                    'supplement_agreement_id': self.supplement_agreement_id.id,
                    'name': change.name,
                    'current_value': change.current_value,
                    'new_value': change.new_value
                }) for change in changes_to_update]})

        return self.supplement_agreement_id.action_submit_approval()
    

class SummaryChangeLine(models.TransientModel):
    _name = 'summary.change.line'
    _description = 'Summary Change Line'

    name = fields.Char(string="Field")
    current_value = fields.Text(string="Current")
    new_value = fields.Text(string="Changes")
    wizard_id = fields.Many2one('summary.change.wizard', required=True)
    bypass_create = fields.Boolean(default=False)