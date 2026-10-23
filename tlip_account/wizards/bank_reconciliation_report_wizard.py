from odoo import api, fields, models, _


class BankReconciliationReportWizard(models.TransientModel):
    _name = 'bank.reconciliation.report.wizard'
    _description = 'Bank Reconciliation Report Wizard'

    def _default_partner_bank(self):
        return self.env['res.partner.bank'].search([]).ids

    reconciliation_date = fields.Date(
        default=fields.Date.today(), required=True)
    partner_bank_ids = fields.Many2many(
        'res.partner.bank', default=_default_partner_bank)

    def button_generate_reconciliation_data(self):
        return self.env['bank.reconciliation.report']._generate_reconciliation_data(
            self.reconciliation_date, self.partner_bank_ids.ids)
