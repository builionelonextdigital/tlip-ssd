# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

SAMPLE_DATA = {
	'01': {'cumulative_account_arising_number_ids': ['5111'], 'corresponding_to_the_account_ids': ['131']},
	'02': {'cumulative_account_arising_number_ids': ['5111'], 'corresponding_to_the_account_ids': ['5211', '5212', '5213']},
	'11': {'cumulative_account_arising_number_ids': ['632'], 'corresponding_to_the_account_ids': ['911']},
	'21': {'cumulative_account_arising_number_ids': ['515'], 'corresponding_to_the_account_ids': ['911']},
	'22': {'cumulative_account_arising_number_ids': ['635'], 'corresponding_to_the_account_ids': ['911']},
	'25': {'cumulative_account_arising_number_ids': ['6411', '6412', '6413', '6414', '6415', '6417', '6418'], 'corresponding_to_the_account_ids': ['911']},
	'26': {'cumulative_account_arising_number_ids': ['6421', '6422', '6423', '6424', '6425', '6426', '6427', '6428'], 'corresponding_to_the_account_ids': ['911']},
	'31': {'cumulative_account_arising_number_ids': ['711'], 'corresponding_to_the_account_ids': ['911']},
	'32': {'cumulative_account_arising_number_ids': ['811'], 'corresponding_to_the_account_ids': ['911']},
	'5182111': {'cumulative_account_arising_number_ids': ['8211'], 'corresponding_to_the_account_ids': ['911']},
	'5182112': {'cumulative_account_arising_number_ids': ['8211'], 'corresponding_to_the_account_ids': ['911']},
	'5282121': {'cumulative_account_arising_number_ids': ['8212'], 'corresponding_to_the_account_ids': ['911']},
	'5282122': {'cumulative_account_arising_number_ids': ['8212'], 'corresponding_to_the_account_ids': ['911']},

}

class BusinessActivitiesResults(models.Model):
	_name = 'business.activities.config'
	_rec_name = 'targets_name'
	_description = 'Business activities config'

	targets_name = fields.Char('Targets Name')
	code = fields.Char('Code')
	cumulative_number_of_arising = fields.Selection([('debtor','Debtor'),('side_has','Side has')])
	cumulative_account_arising_number_ids = fields.Many2many('account.account','cumulative_config', 'cumulative_account_arising_number_id', 'cumulative_config_id',string="Cumulative account arising number")
	corresponding_to_the_account_ids = fields.Many2many('account.account','corresponding_config', 'corresponding_to_the_account_id', 'corresponding_config_id',string="Corresponding to the account")
	default_formula = fields.Text('Default Formula',help="The formula must be configured as follows. Example: S01 - SO2. Explain: S01 in formula is code 01 based on the code configured with the criteria")
	sequence_number_shown_on_report = fields.Integer('Sequence number shown on report')
	follow = fields.Selection([('default_formula','Default Formula'),('derivative_number_accumulation','Derivative Number Accumulation')])
	hide_on_report = fields.Boolean('Hide on report')
	active = fields.Boolean(string="Active", default=True)

	company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)

	def create_missing_field_ids(self):
		if not self._context.get("create_company"):
			for record in self:
				check_exists = self.search([('code', '=', record.code)])
				record_exists = check_exists - record
				if record_exists and len(record_exists) == 1:
					record.update({'active': False})
				elif record_exists and len(record_exists) > 1:
					pass
				else:
					data = SAMPLE_DATA.get(record.code, False)
					if data:
						corresponding_to_the_account_ids = self.env['account.account'].search([('code', 'in', data.get('corresponding_to_the_account_ids', []))]).ids
						cumulative_account_arising_number_ids = self.env['account.account'].search([('code', 'in', data.get('cumulative_account_arising_number_ids', []))]).ids
						record.update({
							'corresponding_to_the_account_ids': [(6, 0, corresponding_to_the_account_ids)],
							'cumulative_account_arising_number_ids': [(6, 0, cumulative_account_arising_number_ids)],
						})
		self.action_duplicate_accounts_company()
	def action_duplicate_accounts_company(self):
		self = self.sudo()
		copy_records = self.env["business.activities.config"]
		if not self._context.get("new_company"):
			companies = self.env["res.company"].search([("id", "!=", self.env.company.id)])
			for record in self:
				for company in companies:
					copy_records += record.sudo().copy({"company_id": company.id})
		else:
			company_id = self.env["res.company"].search([("id", "!=", self._context.get("new_company"))],limit=1,order="create_date asc")
			search_self = self.search([('company_id','=',company_id.id)]) if company_id else False
			for se in search_self:
				data = SAMPLE_DATA.get(se.code, False)
				vals = {"company_id":  self._context.get("new_company")}
				if data:
					corresponding_to_the_account_ids = self.env['account.account'].search([('code', 'in', data.get('corresponding_to_the_account_ids', [])),('company_id','=',self.env.company.id)]).ids
					cumulative_account_arising_number_ids = self.env['account.account'].search([('code', 'in', data.get('cumulative_account_arising_number_ids', [])),('company_id','=',self.env.company.id)]).ids
					vals.update({
						'corresponding_to_the_account_ids': [(6, 0, corresponding_to_the_account_ids)],
						'cumulative_account_arising_number_ids': [(6, 0, cumulative_account_arising_number_ids)],
					})
				se.sudo().copy(vals)

