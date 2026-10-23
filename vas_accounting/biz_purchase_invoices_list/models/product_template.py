# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, RedirectWarning, UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    general_product = fields.Boolean('General Product')
    taxable_product = fields.Boolean('Taxable Product')
    untaxable_products = fields.Boolean('Untaxable Product')
