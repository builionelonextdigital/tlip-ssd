from odoo import models, fields

class IncomeFeeType(models.Model):
    _inherit = 'product.product'

    contract_type_id = fields.Many2one('contract.type', 'Contract Type')