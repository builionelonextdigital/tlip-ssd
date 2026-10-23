from odoo import fields, models


class SignDocumentType(models.Model):
    _inherit = "sign.document.type"

    code = fields.Char(required=False)
