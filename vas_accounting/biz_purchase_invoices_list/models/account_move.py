# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMoveLinePurchase(models.Model):
	_inherit = 'account.move.line'

	product_shared = fields.Boolean("HHDV Shared",compute="_compute_product_shared",readonly=False,store=True)

	@api.depends('product_id')
	def _compute_product_shared(self):
		for res in self:
			res.product_shared = True if res.product_id.general_product else False


	
