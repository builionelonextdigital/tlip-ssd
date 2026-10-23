import base64

from odoo import _, models
from odoo.exceptions import UserError


class SignTicketMixin(models.AbstractModel):
    _inherit = "sign.ticket.mixin"

    def _get_sign_ticket_report_action(self):
        self.ensure_one()
        model_id = self.env["ir.model"]._get_id(self._name)
        report = self.env["ir.actions.report"].search([
            ("binding_model_id", "=", model_id),
            ("report_type", "=", "qweb-pdf"),
        ], limit=1)
        if not report:
            raise UserError(
                _("No PDF report action found for model '%s'.") % self._description
            )
        return report

    def _render_sign_ticket_report_content(self, report):
        self.ensure_one()
        pdf_content, _ = self.env["ir.actions.report"].with_context(
            show_signer_placeholders=True,
        )._render_qweb_pdf(report, self.id)
        return pdf_content

    def _get_sign_ticket_report_filename(self, report):
        self.ensure_one()
        filename = self.display_name or report.name or _("Report")
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"
        return filename

    def _prepare_sign_ticket_document_vals(self):
        self.ensure_one()
        report = self._get_sign_ticket_report_action()
        pdf_content = self._render_sign_ticket_report_content(report)
        return [
            (0, 0, {
                "filename": self._get_sign_ticket_report_filename(report),
                "file": base64.b64encode(pdf_content),
            })
        ]
