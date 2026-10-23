from odoo import fields, models, Command, _


class PurchaseSummaryChangeWizard(models.TransientModel):
    _name = "purchase.summary.change.wizard"
    _description = "Purchase Summary Changes Wizard"

    purchase_supplement_id = fields.Many2one('purchase.supplement', required=True)    
    change_line_ids = fields.One2many('purchase.summary.change.line', 'wizard_id')
    reason = fields.Text(related='purchase_supplement_id.reason', readonly=True)
    effective_date = fields.Date(related='purchase_supplement_id.effective_date', readonly=True)

    def button_confirm(self):
        changes_to_update = self.change_line_ids.filtered(lambda l: not l.bypass_create)
        if changes_to_update:
            self.purchase_supplement_id.write({
                'summary_change_ids': [Command.clear()] + [Command.create({
                    'purchase_supplement_id': self.purchase_supplement_id.id,
                    'name': change.name,
                    'current_value': change.current_value,
                    'new_value': change.new_value
                }) for change in changes_to_update]})

        return self.purchase_supplement_id.action_submit_approval()


class SummaryChangeLine(models.TransientModel):
    _name = 'purchase.summary.change.line'
    _description = 'Summary Change Line'

    name = fields.Char(string="Field")
    current_value = fields.Text(string="Current")
    new_value = fields.Text(string="Changes")
    wizard_id = fields.Many2one('purchase.summary.change.wizard', required=True)
    bypass_create = fields.Boolean(default=False)
