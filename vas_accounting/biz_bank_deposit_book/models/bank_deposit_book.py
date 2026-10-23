from odoo import models, api, fields, _

from odoo.exceptions import ValidationError

class BankDepositBook(models.TransientModel):
	_name = 'bank.deposit.book'
	_desctiption = 'Bank deposit book'

	from_date = fields.Date('From date', required=True)
	to_date = fields.Date('To date', required=True)
	journal_id = fields.Many2one('account.journal', 'Bank journal', domain="[('type','=','bank')]", required=True)

	@api.constrains('to_date','from_date')
	def onchange_from_date(self):
		if self.from_date and self.to_date:
			if self.from_date > self.to_date:
				self.from_date = False
				raise ValidationError(_('From date can not greater than to date'))

	def action_print_pdf(self):
		return self.env.ref('biz_bank_deposit_book.action_rp_bank_deposit_book').report_action(self)

	def action_print_excel(self):
		return self.env.ref('biz_bank_deposit_book.action_rp_bank_deposit_book_xlsx').report_action(self)

	def get_report_name(self):
		def format_date(date):
			return date.strftime('%d/%m/%Y')

		reprot_name = 'Sổ tiền gửi ngân hàng (S08_DN)'
		name = 'None'
		if self.journal_id:
			name = self.journal_id.name

		return  reprot_name + name + "_%s_%s" % (format_date(self.from_date), format_date(self.to_date))