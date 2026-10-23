from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    utility_type = fields.Selection(
        [('electricity', 'Electricity'),
         ('water', 'Water')], string="Utility Type")
