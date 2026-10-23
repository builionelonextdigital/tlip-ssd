from odoo import models, fields


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'

    name = fields.Char('Contract Type', required=True)
    classification = fields.Selection(selection=[
        ('land', 'Land'),
        ('office', 'Office'),
        ('factory', 'Factory'),
        ('meeting_room', 'Meeting Room'),
        ('football_yard', 'Football Yard'),
        ('parking', 'Parking'),
        ('construction', 'Construction Work'),
        ('telecom', 'Telecom'),
        ('principle', 'Principle')
    ], string='Classification', required=True)
    document_template_id = fields.Many2one(
        'docx.template', 'Document Template',
        domain=[('model_id.model', '=', 'leasing.agreement')])
