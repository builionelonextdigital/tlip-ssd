from odoo import models, fields


class ProcurementContractType(models.Model):
    _name = 'purchase.contract.type'
    _description = 'Procurement Contract Type'

    name = fields.Char('Contract Type', required=True)
    classification = fields.Selection(selection=[
        ('goods', 'Goods'),
        ('service', 'Service'),
        ('construction', 'Construction'),
        ('consultant', 'Consultant'),
        ('principle', 'Principle'),
    ], string='Classification', required=True)
    document_template_id = fields.Many2one(
        'docx.template', 'Document Template',
        domain=[('model_id.model', '=', 'purchase.requisition')], required=True)
