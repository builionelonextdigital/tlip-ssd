# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountTax(models.Model):
	_inherit = 'account.tax'

	type_vat = fields.Selection([
			("0_vat", '0 %'),
			("5_vat", '5 %'),
			("8_vat", '8 %'),
			("10_vat", '10 %'),
		], string="Type vat")

