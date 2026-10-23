from odoo import models, fields

class DocumentPreview(models.TransientModel):
    _name = 'document.preview'
    _description = 'Document Preview'

    file = fields.Binary('File', attachment=False)
