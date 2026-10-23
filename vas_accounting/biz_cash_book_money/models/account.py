# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _, osv

class AccountAccount(models.Model):
	_inherit = 'account.account'

	default_journal_ids = fields.One2many("account.journal",'default_account_id')