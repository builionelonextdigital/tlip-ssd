# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


SAMPLE_DATA = {
	'111': {'account_ids': ['1111', '1112', '1113', '1121', '1122', '1123', '1124', '1125', '1126', '1127', '1131']},
	'112': {'account_ids': ['1281', '1288']},
	'121': {'account_ids': ['1211', '1212', '1218']},
	'122': {'account_ids': ['2291']},
	'123': {'account_ids': ['1281', '1282', '1288']},
	'131': {'account_ids': ['131']},
	'132': {'account_ids': ['331']},
	'133': {'account_ids': ['1362', '1363', '1368']},
	'134': {'account_ids': ['337']},
	'135': {'account_ids': ['1283']},
	'136': {'account_ids': ['1385', '1388', '141', '244', '3341', '3348', '3381', '3382', '3383', '3384', '3385', '3386', '3387', '3388']},
	'137': {'account_ids': ['2293']},
	'139': {'account_ids': ['1381']},
	'141': {'account_ids': ['151', '152', '1531', '1532', '1533', '1534', '1541', '1542', '1543', '1544', '1551', '1557', '1561', '1562', '1567', '157', '158']},
	'149': {'account_ids': ['2294']},
	'151': {'account_ids': ['242']},
	'152': {'account_ids': ['1331', '1332']},
	'153': {'account_ids': ['33311', '33312', '3332', '3333', '3334', '3335', '3336', '3337', '33381', '33382', '3339']},
	'154': {'account_ids': ['171']},
	'155': {'account_ids': ['2281']},
	'211': {'account_ids': ['131']},
	'212': {'account_ids': ['331']},
	'213': {'account_ids': ['1361']},
	'214': {'account_ids': ['1362', '1363', '1368']},
	'215': {'account_ids': ['1283']},
	'216': {'account_ids': ['1385', '1388', '141', '244', '3341', '3348', '3381', '3382', '3383', '3384', '3385', '3386', '3387', '3388']},
	'219': {'account_ids': ['2293']},
	'222': {'account_ids': ['2111', '2112', '2113', '2114', '2115', '2118']},
	'223': {'account_ids': ['2141']},
	'225': {'account_ids': ['2121', '2122']},
	'226': {'account_ids': ['2142']},
	'228': {'account_ids': ['2131', '2132', '2133', '2134', '2135', '2136', '2138']},
	'229': {'account_ids': ['2143']},
	'231': {'account_ids': ['217']},
	'232': {'account_ids': ['2147']},
	'241': {'account_ids': ['1541', '1542', '1543', '1544', '2294']},
	'242': {'account_ids': ['2411', '2412', '2413']},
	'251': {'account_ids': ['221']},
	'252': {'account_ids': ['222']},
	'253': {'account_ids': ['2281']},
	'254': {'account_ids': ['2292']},
	'255': {'account_ids': ['1281', '1282', '1288']},
	'261': {'account_ids': ['242']},
	'262': {'account_ids': ['243']},
	'263': {'account_ids': ['1534', '2294']},
	'311': {'account_ids': ['331']},
	'312': {'account_ids': ['131']},
	'313': {'account_ids': ['33311', '33312', '3332', '3333', '3334', '3335', '3336', '3337', '33381', '33382', '3339']},
	'314': {'account_ids': ['3341', '3348']},
	'315': {'account_ids': ['335']},
	'316': {'account_ids': ['3362', '3363', '3368']},
	'317': {'account_ids': ['337']},
	'318': {'account_ids': ['3387']},
	'319': {'account_ids': ['1381', '1385', '1388', '3381', '3382', '3383', '3384', '3385', '3386', '3387', '3388', '344']},
	'320': {'account_ids': ['3411', '3412', '34311']},
	'321': {'account_ids': ['3521', '3522', '3523', '3524']},
	'322': {'account_ids': ['3531', '3532', '3533', '3534']},
	'323': {'account_ids': ['357']},
	'324': {'account_ids': ['171']},
	'331': {'account_ids': ['331']},
	'332': {'account_ids': ['131']},
	'333': {'account_ids': ['335']},
	'334': {'account_ids': ['3361']},
	'335': {'account_ids': ['3362', '3363', '3368']},
	'336': {'account_ids': ['3387']},
	'337': {'account_ids': ['3381', '3382', '3383', '3384', '3385', '3386', '3387', '3388', '344']},
	'338': {'account_ids': ['3411', '34311', '34312', '34313']},
	'339': {'account_ids': ['3432']},
	'340': {'account_ids': ['41112']},
	'341': {'account_ids': ['347']},
	'342': {'account_ids': ['3521', '3522', '3523', '3524']},
	'343': {'account_ids': ['3561', '3562']},
	'411a': {'account_ids': ['41111']},
	'411b': {'account_ids': ['41112']},
	'412': {'account_ids': ['4112']},
	'413': {'account_ids': ['4113']},
	'414': {'account_ids': ['4118']},
	'415': {'account_ids': ['419']},
	'416': {'account_ids': ['412']},
	'417': {'account_ids': ['4131', '4132']},
	'418': {'account_ids': ['414']},
	'419': {'account_ids': ['417']},
	'420': {'account_ids': ['418']},
	'421a': {'account_ids': ['4211', '4212']},
	'421b': {'account_ids': ['4212']},
	'422': {'account_ids': ['441']},
	'431': {'account_ids': ['1611', '1612', '4611', '4612']},
	'432': {'account_ids': ['466']},
}

DATA_CATEG = {'110': {'total_categ_ids': ['111', '112']}, '120': {'total_categ_ids': ['121', '122', '123']},
			  '130': {'total_categ_ids': ['131', '132', '133', '134', '135', '136', '137', '139']},
			  '140': {'total_categ_ids': ['141', '149']},
			  '150': {'total_categ_ids': ['151', '152', '153', '154', '155']},
			  '100': {'total_categ_ids': ['110', '120', '130', '140', '150']},
			  '210': {'total_categ_ids': ['211', '212', '213', '214', '215', '216', '219']},
			  '221': {'total_categ_ids': ['222', '223']}, '224': {'total_categ_ids': ['225', '226']},
			  '227': {'total_categ_ids': ['228', '229']}, '220': {'total_categ_ids': ['221', '224', '227']},
			  '230': {'total_categ_ids': ['231', '232']}, '240': {'total_categ_ids': ['241', '242']},
			  '250': {'total_categ_ids': ['251', '252', '253', '254', '255']},
			  '260': {'total_categ_ids': ['261', '262', '263', '268']},
			  '200': {'total_categ_ids': ['210', '220', '230', '240', '250', '260']},
			  '270': {'total_categ_ids': ['100', '200']}, '310': {
		'total_categ_ids': ['311', '312', '313', '314', '315', '316', '317', '318', '319', '320', '321', '322', '323',
							'324']}, '330': {
		'total_categ_ids': ['331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341', '342', '343']},
			  '300': {'total_categ_ids': ['310', '330']}, '411': {'total_categ_ids': ['411b', '411a']},
			  '421': {'total_categ_ids': ['421a', '421b']}, '410': {
		'total_categ_ids': ['411', '412', '413', '414', '415', '416', '417', '418', '419', '420', '421b', '422']},
			  '430': {'total_categ_ids': ['431', '432']}, '400': {'total_categ_ids': ['410', '430']},
			  '440': {'total_categ_ids': ['300', '400']}}

class AccountingBalanceSheet(models.Model):
	_name = 'accounting.balance.sheet'
	_description = 'Accounting Balance Sheet'
	_rec_name = 'categ_name'
	_order = "code"

	categ_name = fields.Char('Category name')
	stt_calculate = fields.Integer('STT Calculate')
	code = fields.Char('Code')
	parent_level_id = fields.Many2one('accounting.balance.sheet')
	apply_by = fields.Selection([
			('total_categ','Total Category'),
			('total_debit_credit', 'Total Debit -  Credit by account'),
			('total_credit_debit', 'Total Credit -  Debit by account'),
			('residual_value_debt','Take the residual value of the debt in arising'),
			('residual_value_credit','Get the residual value on arise'),
		], string="Apply by")

	report_type = fields.Selection(selection=[('accounting_balance_sheet', 'Accounting Balance Sheet')], string="Report Type", default="accounting_balance_sheet")

	active = fields.Boolean(string="Active", default=True)

	account_ids = fields.Many2many('account.account','rel_balance_account','balance_id','account_id', string="Account systems")
	total_categ_ids = fields.Many2many('accounting.balance.sheet','rel_blance_total_categ','balance_id','total_categ_id', string="Total Categorys")
	in_business_cycle = fields.Boolean('In the business cycle')
	follow_by_partner = fields.Boolean('Follow by partner')

	company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)
	is_bold_report = fields.Boolean('Bold in report')
	value_on_report = fields.Selection([
		('always_positive', 'Always positive'),
		('zero_when_negative', 'Equals 0 when the result is negative')
	], string="Value on report")

	def create_missing_field_ids(self):
		try:
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
							account_ids = self.env['account.account'].search([('code', 'in', data.get('account_ids', []))]).ids
							record.update({
								'account_ids': [(6, 0, account_ids)],
							})
			self.action_duplicate_accounts_company()
		except Exception as err:
			print("err", err)

	def action_duplicate_accounts_company(self):
		self = self.sudo()
		copy_records = self.env["accounting.balance.sheet"]
		if not self._context.get("new_company"):
			companies = self.env["res.company"].search([("id", "!=", self.env.company.id)])
		else:
			company_id = self.env["res.company"].search([("id", "!=", self._context.get("new_company"))],limit=1,order="create_date asc")
			search_self = self.search([('company_id','=',company_id.id)]) if company_id else False
			for se in search_self:
				data = SAMPLE_DATA.get(se.code, False)
				data_account_ids = [(6, 0, [])]
				if data:
					account_ids = self.env['account.account'].search([('code', 'in', data.get('account_ids', []))]).ids
					data_account_ids =  [(6, 0, account_ids)]

				copy_records += se.copy({"company_id": self._context.get("new_company"), "total_categ_ids": [(6, 0, [])],"account_ids": data_account_ids})
		for record in self:
			for company in companies:
				copy_records += record.copy({"company_id": company.id, "total_categ_ids": [(6, 0, [])]})
		for record in copy_records:
			data = DATA_CATEG.get(record.code, False)
			if data:
				total_categ_ids = copy_records.filtered_domain([("code", "in", data.get("total_categ_ids"))])
				record.update({"total_categ_ids": [(6, 0, total_categ_ids.ids)]})


class AccountingBalanceSheetTemplate(models.Model):
	_name = 'accounting.balance.template'
	_description = 'Accounting Balance Template'

	name = fields.Char('Name')
	template_type = fields.Selection(selection=[('accounting_balance_sheet', 'Accounting Balance Sheet')], default='accounting_balance_sheet', string="Template Type")
	# Old
	line_ids = fields.One2many('accounting.balance.template.line','template_id')
	# New
	balance_ids = fields.Many2many(comodel_name='accounting.balance.sheet', relation='accounting_balance_template_sheet_rel', column1='template_id', column2='sheet_id', domain="[('report_type', '=', template_type)]")
	company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)

class AccountingBalanceSheetTemplateLine(models.Model):
	_name = 'accounting.balance.template.line'
	_description = 'Accounting Balance Template Line'

	template_id = fields.Many2one('accounting.balance.template')
	balance_id = fields.Many2one('accounting.balance.sheet','Assets', required=True)
	code = fields.Char('Code')

	@api.onchange('balance_id')
	def onchange_balance_id(self):
		if self.balance_id:
			self.code = self.balance_id.code