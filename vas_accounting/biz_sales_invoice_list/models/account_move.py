# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	product_not_taxable = fields.Boolean("HHDV is not taxable",compute="_compute_product_not_taxable",readonly=False,store=True)

	@api.depends('product_id')
	def _compute_product_not_taxable(self):
		for res in self:
			res.product_not_taxable = True if res.product_id.product_not_taxable else False


	
