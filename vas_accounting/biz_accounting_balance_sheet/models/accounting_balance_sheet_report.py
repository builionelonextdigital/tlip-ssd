# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class AccountingBalanceSheetReport(models.Model):
	_name = 'accounting.balance.sheet.report'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_description = 'Accounting Balance Sheet'

	def default_template_id(self):
		template_id = self.env['accounting.balance.template'].search(
		    [], order="id desc", limit=1)
		return template_id and template_id.id or False

	previous_id = fields.Many2one(
	    'accounting.balance.sheet.report', 'Previous period')
	from_date = fields.Date('From Date', required=True)
	to_date = fields.Date('To Date', required=True)
	template_id = fields.Many2one(
	    'accounting.balance.template', 'Template', default=default_template_id)
	line_ids = fields.One2many(
	    'accounting.balance.sheet.report.line', 'report_id')
	state = fields.Selection([
			('draft', 'Draft'),
			('closed', 'Closed'),
		], string="State", default='draft')
	company_id = fields.Many2one(comodel_name="res.company",
	                             string="Company", default=lambda self: self.env.company)

	@api.depends('from_date', 'to_date')
	def _compute_display_name(self):
		for report in self:
			if report.from_date and report.to_date:
				report.display_name = _('Bảng cân đối kế toán: %s - %s') % (
					report.from_date.strftime('%d/%m/%Y'),
					report.to_date.strftime('%d/%m/%Y')
				)
			else:
				report.display_name = 'New'

	@api.onchange('template_id')
	def onchange_template_id(self):
		for rec in self:
			template = rec.template_id
			if rec.line_ids:
				rec.line_ids.unlink()
			if rec.template_id and rec.template_id.balance_ids:
				rec.line_ids = [(0, 0, {
						'balance_id': line and line.id or False,
						'code': line.code
					}) for line in rec.template_id.balance_ids]
			rec.template_id = template

	def action_calculate(self):
		business_cycle = self.env.company.business_cycle or 0

		def find_move_line(line, domain_add=[]):
			domain = [
				('date', '>=', self.from_date),
				('date', '<=', self.to_date),
				('account_id', 'in', line.balance_id.account_ids.ids),
				('parent_state', '=', 'posted'),
			] + domain_add
			if line.balance_id.in_business_cycle:
				domain += ["|", ('date_maturity', '=', False), ('date_maturity', '<=', self.to_date + relativedelta(months=business_cycle))] \
					if line.balance_id.in_business_cycle else [('date_maturity', '>', self.to_date + relativedelta(months=business_cycle))]
			return self.env['account.move.line'].search(domain)

		def find_last_year_previous(line):
			if self.previous_id:
				lines = self.previous_id.line_ids.filtered(lambda x: x.code == line.code)
				return sum(lines.mapped('number_last_year')) if lines else 0
			return 0

		for line in self.line_ids.filtered(lambda x: x.balance_id and x.balance_id.apply_by != 'total_categ'):
			movelines = []
			number_last_year = 0
			# lấy giá trị cuối năm của kỳ trước khớp  với dòng đang tính
			number_first_year = find_last_year_previous(line)
			if line.balance_id.apply_by in ['total_debit_credit', 'total_credit_debit']:
				movelines = find_move_line(line)
				debit = movelines and sum(movelines.mapped('debit')) or 0
				credit = movelines and sum(movelines.mapped('credit')) or 0
				# loại Tổng Nợ - Có theo tài khoản thì nợ trừ có, loại Tổng Có - Nợ theo tài khoản thì có - nợ
				number_last_year = debit - \
				    credit if line.balance_id.apply_by == 'total_debit_credit' else credit - debit

			if line.balance_id.apply_by in ['residual_value_debt', 'residual_value_credit']:
				movelines = find_move_line(line)
				
				# --- LOGIC MỚI: XỬ LÝ JSON TỪ KỲ TRƯỚC ---
				partner_data = {}
				# Reset number_first_year để tính toán lại chính xác từ JSON
				number_first_year = 0
				if self.previous_id:
					prev_line = self.previous_id.line_ids.filtered(lambda x: x.code == line.code)
					if prev_line and prev_line.partner_balance_data:
						partner_data = json.loads(prev_line.partner_balance_data)
				# Tính Số dư Đầu kỳ: Quét qua Từng tài khoản -> Từng đối tượng
				for acc_id_str, p_dict in partner_data.items():
					for p_id_str, vals in p_dict.items():
						if line.balance_id.apply_by == 'residual_value_debt':
							balance = vals['debit'] - vals['credit']
						else:
							balance = vals['credit'] - vals['debit']
						
						# Bảng cân đối: dư Nợ/Có phải > 0 mới lấy
						if balance > 0:
							number_first_year += balance

				# Duyệt các phát sinh trong kỳ này, nhóm theo Tài khoản trước
				for group in movelines.grouped('account_id').items():
					acc_id_str = str(group[0].id) if group[0] else '0'
					# Khởi tạo dict cho Tài khoản nếu chưa có trong JSON
					if acc_id_str not in partner_data:
						partner_data[acc_id_str] = {}
					if line.balance_id.follow_by_partner:
						# Khởi tạo dict cho Tài khoản nếu chưa có trong JSON
						if acc_id_str not in partner_data:
							partner_data[acc_id_str] = {}

						group_partner = group[1].grouped('partner_id').items()
						for partner_group in group_partner:
							p_id_str = str(partner_group[0].id) if partner_group[0] else '0'
							
							debit = sum(partner_group[1].mapped('debit')) or 0
							credit = sum(partner_group[1].mapped('credit')) or 0
							
							# Khởi tạo số dư cho Đối tượng trong Tài khoản này nếu chưa có
							if p_id_str not in partner_data[acc_id_str]:
								partner_data[acc_id_str][p_id_str] = {'debit': 0.0, 'credit': 0.0}
							
							# Cộng dồn phát sinh của đối tượng thuộc tài khoản này
							partner_data[acc_id_str][p_id_str]['debit'] += debit
							partner_data[acc_id_str][p_id_str]['credit'] += credit
					else:
						debit = sum(group[1].mapped('debit')) or 0
						credit = sum(group[1].mapped('credit')) or 0
						# Cộng dồn phát sinh của tài khoản này (không phân biệt đối tượng)
						if '0' not in partner_data[acc_id_str]:
							partner_data[acc_id_str]['0'] = {'debit': 0.0, 'credit': 0.0}
						partner_data[acc_id_str]['0']['debit'] += debit
						partner_data[acc_id_str]['0']['credit'] += credit

				# --- TÍNH SỐ DƯ CUỐI KỲ CỘNG DỒN TỪ JSON ---
				if line.balance_id.follow_by_partner:
					for acc_id_str, p_dict in partner_data.items():
						for p_id_str, vals in p_dict.items():
							if line.balance_id.apply_by == 'residual_value_debt':
								balance = vals['debit'] - vals['credit']
							else:
								balance = vals['credit'] - vals['debit']
							
							# Chỉ cộng vào báo cáo Bảng Cân Đối nếu số dư > 0
							number_last_year += balance if balance > 0 else 0
				elif line.balance_id.apply_by in ['residual_value_debt', 'residual_value_credit']:
					for acc_id_str, p_dict in partner_data.items():
						debit = sum(vals['debit'] for vals in p_dict.values())
						credit = sum(vals['credit'] for vals in p_dict.values())
						if line.balance_id.apply_by == 'residual_value_debt':
							balance = debit - credit
						else:
							balance = credit - debit
						number_last_year += balance if balance > 0 else 0

            # XÁC ĐỊNH SỐ DƯ CUỐI CÙNG LÊN BÁO CÁO
			if line.balance_id.follow_by_partner or line.balance_id.apply_by in ['residual_value_debt', 'residual_value_credit']:
				# Lúc này number_last_year đã là số lũy kế đối trừ từ lúc ban đầu
				number_last = number_last_year 
			else:
				number_last = number_last_year + number_first_year
			
			if line.balance_id.value_on_report == 'always_positive':
				number_last = abs(number_last)
			if line.balance_id.value_on_report == 'zero_when_negative':
				if number_last < 0:
					number_last = 0

			# Ghi nhận JSON data để luân chuyển sang kỳ sau
			json_data_to_save = json.dumps(partner_data) if line.balance_id.follow_by_partner or line.balance_id.apply_by in ['residual_value_debt', 'residual_value_credit'] else False

			line.write({
				'number_first_year': number_first_year,
				'number_last_year': number_last,
				'move_line_ids': [(6,0, movelines and movelines.ids or [])],
				'partner_balance_data': json_data_to_save,
			})

		for line in self.line_ids.filtered(lambda x: x.balance_id and x.balance_id.apply_by == 'total_categ').sorted(lambda x: x.balance_id.stt_calculate):
			line_ids = self.line_ids.filtered(lambda x: x.balance_id.id in line.balance_id.total_categ_ids.ids)
			number_first_year = find_last_year_previous(line) #lấy giá trị cuối năm của kỳ trước khớp  với dòng đang tính
			number_last_year = sum(line_ids.mapped('number_last_year')) if line_ids else 0

			line.write({
				'number_first_year':number_first_year,
				'number_last_year':number_last_year,
				'move_line_ids': [(6,0, line_ids and line_ids.move_line_ids.ids or [])]
			})

	def unlink(self):
		for res in self:
			if res.state == 'closed':
				raise ValidationError(_('You cannot delete data in closed state'))

		return super(AccountingBalanceSheetReport, self).unlink()

	def action_closed(self):
		self.write({
			'state': 'closed'
		})

	def action_open(self):
		self.write({
			'state': 'draft'
		})

	def action_view_detail(self):
		action = self.env["ir.actions.actions"]._for_xml_id("biz_accounting_balance_sheet.action_accounting_balance_sheet_report_line")
		action['domain'] = [('id','in', self.line_ids.ids)]
		return action

class AccountingBalanceSheetReportLine(models.Model):
	_name = 'accounting.balance.sheet.report.line'
	_description = 'Accounting Balance Sheet Line'

	report_id = fields.Many2one('accounting.balance.sheet.report')
	balance_id = fields.Many2one('accounting.balance.sheet','Assets')
	code = fields.Char('Code')
	number_first_year = fields.Float('Beginning Balance')
	number_last_year = fields.Float('Ending Balance')
	move_line_ids = fields.Many2many('account.move.line',string="Account move line", readonly=True)
	apply_by = fields.Selection(related="balance_id.apply_by", readonly=True)
	partner_balance_data = fields.Text('Partner Balance JSON', readonly=True)

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
					if key in ['report_id', 'move_line_ids', 'apply_by', 'partner_balance_data']:
						continue

					name = self.env['ir.model.fields'].get_field_string(self._name)[key]
					old_value = res[key]
					new_value = val
					if key == 'balance_id':
						old_value = res[key].display_name
						new_value = self.env['accounting.balance.sheet'].browse(val).display_name

					if new_value != old_value:
						check = True
						msg += "<li> %s: %s -> %s"  % (name, old_value, new_value)
				msg += "</ul>"
				if check and res.report_id:
					res.report_id.message_post(body=msg) 

		return super().write(vals)
	
	def view_move_line(self):
		return {
            'type': 'ir.actions.act_window',
            'name': _('Move line detail'),
            'res_model': 'account.move.line',
            'view_mode': 'list',
            'domain': [('id','in', self.move_line_ids.ids)]
		}