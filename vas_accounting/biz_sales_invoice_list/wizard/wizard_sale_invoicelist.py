# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WizardSaleInvoiceList(models.TransientModel):
	_name = 'wizard.sale.invoicelist'
	_description = 'Sales invoice list'

	from_date = fields.Date('From date', required=True)
	to_date = fields.Date('To date', required=True)

	def action_print(self):
		return self.env.ref('biz_sales_invoice_list.action_report_invoice_list_xlsx').report_action(self)