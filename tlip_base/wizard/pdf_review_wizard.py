from odoo import api, fields, models, _

class PDFReviewWizard(models.TransientModel):
    _name = 'pdf.review.wizard'
    _description = 'PDF Review Wizard'

    pdf_document = fields.Binary(string='PDF Document', store=True)
