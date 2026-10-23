from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    e_signature_file = fields.Binary('E-Signature', attachment=True)
    e_signature_filename = fields.Char('E-Signature Filename')
