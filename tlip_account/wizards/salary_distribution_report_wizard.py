# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WizardSalaryDistributionReport(models.TransientModel):
	_name = 'salary.distribution.report.wizard'
	_description = 'Salary Distribution Report Wizard'

	from_date = fields.Date('From date', required=True)
	to_date = fields.Date('To date', required=True)

	def action_print(self):
		return self.env.ref('tlip_account.action_report_salary_distribution_report_xlsx').report_action(self)