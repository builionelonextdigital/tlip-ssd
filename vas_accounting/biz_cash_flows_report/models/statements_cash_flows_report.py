# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class StatementsCashFlowsReport(models.Model):
	_name = 'statements.cash.flows.report'
	_description = 'Statements Of Cash Flows Report'

	def default_template_id(self):
		template_id = self.env['cash.flows.template'].search([('template_type','=','statements_cash_flows')], order="id desc", limit=1)
		return template_id and template_id.id or False

	name = fields.Char(string="Name")
	previous_id = fields.Many2one('statements.cash.flows.report','Previous period')
	from_date = fields.Date('From Date', required=True)
	to_date = fields.Date('To Date', required=True)
	template_id = fields.Many2one('cash.flows.template','Template', default=default_template_id)
	line_ids = fields.One2many('statements.cash.flows.report.line','report_id')
	state = fields.Selection([
			('draft','Draft'),
			('closed','Closed'),
		],string="State", default='draft')
	company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)

	@api.onchange('template_id')
	def onchange_template_id(self):
		for res in self:
			template = res.template_id
			if res.line_ids:
				res.line_ids.unlink()
			if res.template_id and res.template_id.cash_flows_ids:
				res.line_ids = [(0, 0, {
					'balance_id': line and line.id or False,
					'code': line.code
				}) for line in template.cash_flows_ids]
			res.template_id = template


	def action_calculate(self):
		if self.to_date < self.from_date:
			raise ValidationError(_('Unable to calculate data for the selected time period'))
		line_ids = self.line_ids.filtered(lambda x: x.balance_id and x.balance_id.report_type == 'statements_cash_flows')
		for line in line_ids.filtered(lambda x: x.balance_id.apply_by == 'according_method_of_create'):
			number_first_year = number_last_year = 0
			movelines = self.env['account.move.line'].search([
					# ('journal_id.type','in',['bank','cash']),
					('date','>=', self.from_date),
					('date','<=', self.to_date),
				])
			movelines3 = self.env['account.move.line']
			for move in movelines.filtered(lambda x: x.debit > 0):
				for balance in line.balance_id.line_ids:
					if move.account_id.id in balance.account_number_import_ids.ids:
						if any(line.account_id.id in balance.reciprocal_account_import_ids.ids for line in move.move_id.line_ids):
							if balance.diary_book_ids:
								if move.journal_id.id in balance.diary_book_ids.ids:
									movelines3 += move
							else:
								movelines3 += move
			movelines4 = self.env['account.move.line']
			for move in movelines.filtered(lambda x: x.id not in movelines3.ids and x.credit > 0):
				
				for balance in line.balance_id.line_ids:
					if move.account_id.id in balance.account_number_export_ids.ids:
						if any(line.account_id.id in balance.reciprocal_account_export_ids.ids for line in move.move_id.line_ids):
							if balance.diary_book_ids:
								if move.journal_id.id in balance.diary_book_ids.ids:
									movelines4 += move 
							else:
								movelines4 += move
			debit = 0
			for move in movelines3:
				debit += move.debit

			credit = 0
			for move in movelines4:
				credit += move.credit

			number_first_year = debit - credit

			if self.previous_id and self.previous_id.state == 'closed':
				lines = self.previous_id.line_ids.filtered(lambda x: x.code == line.code)
				if lines:
					number_last_year = sum(lines.mapped('number_first_year'))
			#
			# search_id = self.env['statements.cash.flows.report'].search([
			# 		('id','<',self.id),
			# 		('state','=','closed')], order="id desc", limit=1)
			# if search_id:
			# 	lines = search_id.line_ids.filtered(lambda x: x.balance_id == line.balance_id).sorted(lambda r: r.create_date, reverse=True)
			# 	number_last_year = lines[0].number_first_year if lines else 0
			move_total = movelines3 + movelines4
			line.write({
				'number_first_year': number_first_year,
				'number_last_year': number_last_year,
				'move_line_ids': [(6, 0, move_total and move_total.ids or [])]
			})
		
		for line in line_ids.filtered(lambda x: x.balance_id.apply_by == 'accounting_balance_sheet'):
			targets = self.env['accounting.balance.sheet.report.line'].search([('balance_id','=',line.balance_id.target_id.id),
																			('report_id.from_date','=',self.from_date),
																			('report_id.to_date','=',self.to_date)])
			if line.balance_id.column == 'number_first_year':
				line.number_first_year = sum(targets.mapped('number_first_year')) if targets else 0
			if line.balance_id.column == 'number_last_year':
				line.number_first_year = sum(targets.mapped('number_last_year')) if targets else 0
			if self.previous_id and self.previous_id.state == 'closed':
				lines = self.previous_id.line_ids.filtered(lambda x: x.code == line.code)
				if lines:
					line.number_last_year = sum(lines.mapped('number_first_year'))

		for line in line_ids.filtered(lambda x: x.balance_id.apply_by == 'total_categ'):
			number_first_year = number_last_year = 0
			for lines in line_ids.filtered(lambda x: x.balance_id.id in line.balance_id.total_categ_ids.ids):
				number_first_year += lines.number_first_year
				number_last_year += lines.number_last_year
			line.number_first_year = number_first_year
			line.number_last_year = number_last_year



	def unlink(self):
		for res in self:
			if res.state == 'closed':
				raise ValidationError(_('You cannot delete data in closed state'))

		return super(StatementsCashFlowsReport, self).unlink()

	def action_closed(self):
		self.write({
			'state': 'closed'
		})

	def action_open(self):
		self.write({
			'state': 'draft'
		})

class StatementsCashFlowsReportLine(models.Model):
	_name = 'statements.cash.flows.report.line'
	_description = 'Statements Of Cash Flows Report Line'
	_order = "stt_calculate"

	report_id = fields.Many2one('statements.cash.flows.report')
	balance_id = fields.Many2one('cash.flows','Assets')
	code = fields.Char('Code')
	number_first_year = fields.Float('Beginning Balance')
	move_line_ids = fields.Many2many('account.move.line',string="Account move line", readonly=True)
	number_last_year = fields.Float('Ending Balance')
	apply_by = fields.Selection(related="balance_id.apply_by", readonly=True)
	stt_calculate = fields.Integer('STT Calculate', related="balance_id.stt_calculate")

	@api.onchange('balance_id')
	def onchange_balance_id(self):
		if self.balance_id:
			self.code = self.balance_id.code

	def write(self, vals):
		context = self._context
		if not context.get('pass_log', False):
			for res in self:
				check = False
				msg = "<b>" + _("Assets: %s"  % res.balance_id.display_name ) + "</b><ul>"
				for key, val in vals.items():
					if key in ['report_id','move_line_ids','apply_by']:
						continue

					name = self.env['ir.model.fields'].get_field_string(self._name)[key]
					old_value = res[key]
					new_value = val
					if key == 'balance_id':
						old_value = res[key].display_name
						new_value = self.env['cash.flows'].browse(val).display_name

					if new_value != old_value:
						check = True
						msg += "<li> %s: %s -> %s"  % (name, old_value, new_value)
				msg += "</ul>"
				# if check and res.report_id:
				# 	res.report_id.message_post(body=msg)

		return super().write(vals)

	def view_move_line(self):
		return {
			'type': 'ir.actions.act_window',
			'name': _('Move line detail'),
			'res_model': 'account.move.line',
			'view_mode': 'list',
			'domain': [('id', 'in', self.move_line_ids.ids)]
		}
