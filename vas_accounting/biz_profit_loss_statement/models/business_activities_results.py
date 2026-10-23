# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re
from odoo.tools.safe_eval import safe_eval

class BusinessActivitiesResults(models.Model):
	_name = 'business.activities.results'
	_description = 'Business activities results'

	@api.model
	def default_get(self, default_fields):
		res = super(BusinessActivitiesResults, self).default_get(default_fields)
		search_config = self.env['business.activities.config'].search([('id','!=',False), ('company_id','=',self.env.company.id)])
		vals = []
		for se in search_config:
			vals.append((0,0,{'target_config_id':se.id, 'code': se.code,'hide_view': se.hide_on_report}))
		res.update({'business_activities_results_line_ids': vals})

		return res

	name = fields.Char('Name report', compute="compute_name", store=True)
	state = fields.Selection([('draft','Draft'),('closed','Closed')])
	previous_period_id = fields.Many2one('business.activities.results',domain=[('state','=','closed')],\
		string="Previous period")
	date_to = fields.Date('Date to',required=True)
	date_from = fields.Date('Date From',required=True)
	business_activities_results_line_ids = fields.One2many('business.activities.results.line','business_result_id',\
		'Business activities results line',domain=[('hide_view','=',False)])

	business_activities_results_hide_ids = fields.One2many('business.activities.results.line','business_result_id',\
		'Business activities results line')

	target_count = fields.Integer('',compute="_compute_target_count")
	company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)

	@api.depends("date_to",'date_from')
	def compute_name(self):
		for res in self:
			name = 'Báo cáo hoạt động kinh doanh'
			YMD = '%d/%m/%Y'
			if res.date_to and res.date_from:
				name += " (%s - %s)" % (res.date_from.strftime(YMD), res.date_to.strftime(YMD)) 
			res.name = name
			
	def _compute_target_count(self):
		for res in self:
			res.target_count = 0
			search_config = self.env['business.activities.results.line'].search([('business_result_id','=',res.id)])
			if search_config:
				res.target_count = len(search_config)

	def view_target(self):
		search_config = self.env['business.activities.results.line'].search([('business_result_id','=',self.id)])
		return {
			'name': _('Chi tiết'),
			'view_mode': 'list',
			'res_model': 'business.activities.results.line',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', search_config.ids)],
			'target':'current'
		}

	@api.model
	def create(self,vals):
		res = super(BusinessActivitiesResults,self).create(vals)
		if 'date_to' in vals:
			search_all_date_to = self.search([('id','!=',res.id),('date_to','>=',res.date_to),('date_from','<=',res.date_to)])

		if  'date_from' in vals:
			search_all_date_from = self.search([('id','!=',res.id),('date_to','>=',res.date_from),('date_from','<=',res.date_from)])

		if search_all_date_to or search_all_date_from:
			raise ValidationError('Từ ngày lựa chọn đã được tính toán trước đó, vui lòng kiểm tra lại')
		res.state = 'draft'

		return res

	def write(self,vals):
		if 'date_to' in vals:
			search_all_date_to = self.search([('id','!=',self.id),('date_to','>=',self.date_to),('date_from','<=',self.date_to)])
			if search_all_date_to:
				raise ValidationError('Từ ngày lựa chọn đã được tính toán trước đó, vui lòng kiểm tra lại')
		if 'date_from' in vals:
			search_all_date_from = self.search([('id','!=',self.id),('date_to','>=',self.date_from),('date_from','<=',self.date_from)])
			if search_all_date_from:
				raise ValidationError('Từ ngày lựa chọn đã được tính toán trước đó, vui lòng kiểm tra lại')

		return super(BusinessActivitiesResults,self).write(vals)

	@api.onchange('date_from')
	def onchange_previous_period(self):
		search_previous_period = self.search([('id','!=',False),('date_to','<',self.date_from)], order="id desc",limit=1)
		self.previous_period_id = search_previous_period.id

	def button_calculate(self):
		for value in [True,False]:#calculate hide_view before
			self.button_calculate_common(value)


	def button_calculate_common(self,hide_view):
		for res in self.business_activities_results_hide_ids.filtered(lambda x: x.hide_view == hide_view):
			domain = [('id','!=',False),('date','>=',self.date_from),\
				('date','<=',self.date_to),('account_id','in',res.target_config_id.cumulative_account_arising_number_ids.ids)\
				,('parent_state','=','posted')] 

			if res.target_config_id.corresponding_to_the_account_ids:
				domain += [('move_id.line_ids.account_id','in',res.target_config_id.corresponding_to_the_account_ids.ids)]
			if res.target_config_id.cumulative_number_of_arising == 'debtor':
				domain += [('debit','!=',0)]
			if res.target_config_id.cumulative_number_of_arising == 'side_has':
				domain += [('credit','!=',0)]

			search_journal_detail = self.env['account.move.line'].search(domain)
			sum_all = 0.0
			if  res.target_config_id.follow == 'derivative_number_accumulation':
				if res.target_config_id.cumulative_number_of_arising == 'debtor':
					sum_all = sum(search_journal_detail.mapped('debit')) if search_journal_detail else 0
					
				if res.target_config_id.cumulative_number_of_arising == 'side_has':
					sum_all = sum(search_journal_detail.mapped('credit')) if search_journal_detail else 0
				res.this_year = sum_all


			if res.target_config_id.follow == 'default_formula' and res.target_config_id.default_formula:
				new_string = str(res.target_config_id.default_formula)
				new_result = re.findall('[0-9]+',new_string)
				
				vals = {}
				for new in new_result:
					vals['S' + new] = sum(self.business_activities_results_hide_ids.filtered\
						(lambda x: x.code == new.replace('S','')).mapped('this_year'))

				result = 0
				try:
					result = safe_eval(new_string, vals)
				except Exception as e:
					raise ValidationError('Error: e %s at line %s with formula %s'%(str(e),res.target_config_id.targets_name,new_string))
				res.this_year = float(result)

			for pre in self.previous_period_id.business_activities_results_hide_ids:
				if res.target_config_id == pre.target_config_id:
					res.year_ago = pre.this_year


	def change_state(self):
		self.state = 'closed'

	def button_open(self):
		self.state = 'draft'


class BusinessActivitiesResultsLine(models.Model):
	_name = 'business.activities.results.line'
	_description = 'Business activities results line'

	business_result_id = fields.Many2one('business.activities.results')
	target_config_id = fields.Many2one('business.activities.config',string="Target")
	code = fields.Char('Code')
	present = fields.Char('Present')
	this_year = fields.Float('This year')
	year_ago = fields.Float('Year Ago')
	number = fields.Integer(related='target_config_id.sequence_number_shown_on_report',string='Sequence')
	hide_view = fields.Boolean('')
	check_detail = fields.Boolean('Check',compute="_compute_check_detail")
	check_visible = fields.Boolean('Check Visible',compute="_compute_check_visible",store=True)

	@api.depends('target_config_id')
	def _compute_check_visible(self):
		for res in self:
			res.check_visible = True if res.target_config_id.hide_on_report else False

	def _compute_check_detail(self):
		for res in self:
			search_journal_detail = res._search_account()
			res.check_detail = True if search_journal_detail else False
	
	def _search_account(self):
		array = []
		array_corresponding = []

		for cum in self.target_config_id.cumulative_account_arising_number_ids:
			array.append(cum.id)
		domain = [('id','!=',False),('date','>=',self.business_result_id.date_from),\
			('date','<=',self.business_result_id.date_to),('account_id','in',array)\
			,('parent_state','=','posted')] 
		for corr in self.target_config_id.corresponding_to_the_account_ids:
			array_corresponding.append(corr.id)

		if array_corresponding:
			domain += [('move_id.line_ids.account_id','in',array_corresponding)]
		if self.target_config_id.cumulative_number_of_arising == 'debtor':
			domain += [('debit','!=',0)]
		if self.target_config_id.cumulative_number_of_arising == 'side_has':
			domain += [('credit','!=',0)]

		search_journal_detail = self.env['account.move.line'].search(domain)

		return search_journal_detail

	def detail_account(self):
		search_journal_detail = self._search_account()
		return {
			'name': _('Chi tiết'),
			'view_mode': 'list',
			'res_model': 'account.move.line',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', search_journal_detail.ids)],
			'target':'current'
		}
