from odoo import _, models


class SignDocument(models.Model):
    _inherit = "sign.document"

    def action_preview(self):
        self.ensure_one()
        wizard = self.env['pdf.review.wizard'].create({
            'pdf_document': self.file
        })
        return {
            'name': _('PDF Preview'),
            'view_mode': 'form',
            'res_model': 'pdf.review.wizard',
            'res_id': wizard.id,
            'views': [(self.env.ref('tlip_base.pdf_review_wizard_wizard_form_view').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(self.env.context)
        }
