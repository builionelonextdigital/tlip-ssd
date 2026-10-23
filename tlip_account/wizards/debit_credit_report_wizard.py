# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WizardDebitCreditReport(models.TransientModel):
	_name = 'debit.credit.report.wizard'
	_description = 'Debit Credit Report Wizard'

	from_date = fields.Date('From date', required=True)
	to_date = fields.Date('To date', required=True)

	def action_print(self):
		return self.env.ref('tlip_account.action_report_debit_credit_control_list_xlsx').report_action(self)