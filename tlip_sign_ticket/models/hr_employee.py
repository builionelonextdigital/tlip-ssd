from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    e_signature_file = fields.Binary('E-Signature', attachment=True)
    e_signature_filename = fields.Char('E-Signature Filename')
    initial_signature_file = fields.Binary('Initial Signature', attachment=True)
    initial_signature_filename = fields.Char('Initial Signature Filename')
