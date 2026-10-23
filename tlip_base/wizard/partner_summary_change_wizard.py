from odoo import fields, models, Command, _


class PartnerSummaryChangeWizard(models.TransientModel):
    _name = "partner.summary.change.wizard"
    _description = "Partner Summary Changes Wizard"

    partner_cr_id = fields.Many2one('res.partner.cr', required=True)    
    change_line_ids = fields.One2many('partner.summary.change.line', 'wizard_id')
    reason = fields.Text(related='partner_cr_id.reason', readonly=True)
    effective_date = fields.Date(related='partner_cr_id.effective_date', readonly=True)

    def button_confirm(self):
        changes_to_update = self.change_line_ids
        if changes_to_update:
            self.partner_cr_id.write({
                'summary_change_ids': [Command.clear()] + [Command.create({
                    'partner_cr_id': self.partner_cr_id.id,
                    'name': change.name,
                    'current_value': change.current_value,
                    'new_value': change.new_value
                }) for change in changes_to_update]})

        return self.partner_cr_id.action_submit_approval()


class SummaryChangeLine(models.TransientModel):
    _name = 'partner.summary.change.line'
    _description = 'Summary Change Line'

    name = fields.Char(string="Field")
    current_value = fields.Text(string="Current")
    new_value = fields.Text(string="Changes")
    wizard_id = fields.Many2one('partner.summary.change.wizard', required=True)
