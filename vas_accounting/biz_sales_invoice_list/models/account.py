# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountAccount(models.Model):
	_inherit = 'account.account'

	is_output_vat = fields.Boolean("Is output VAT")