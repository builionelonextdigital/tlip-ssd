from typing import Literal

from odoo import _, fields, models
from odoo.exceptions import UserError


class SignPdfMixin(models.AbstractModel):
    _name = "sign.pdf.mixin"
    _description = "Sign PDF Mixin"
    _inherit = ["pdf.signature.mixin"]

    report_attachment_id = fields.Many2one(
        "ir.attachment", string="Report Attachment", copy=False
    )

    def action_stamp_report(
        self,
        signature_img,
        report_attachment=None,
        skip_if_no_attachment=True,
        direction: Literal['horizontal', 'vertical'] = 'horizontal',
        offset: float = 0,
        sig_width: float = 75,
        sig_height: float = 55,
    ):
        """Sign the generated PDF report for each record in self."""
        for record in self:
            """Sign the PDF report attachment using the employee's e-signature."""
            if not signature_img:
                return

            report_attachment = report_attachment or record._get_attachment_report()
            if not report_attachment:
                if skip_if_no_attachment:
                    return
                raise UserError(_("No report attachment found for signing."))

            signed_pdf = record.sign_pdf(
                keyword=record._get_temporary_word(),
                signature_img_b64=signature_img,
                encoded_pdf=report_attachment.datas,
                stamp_img_b64=signature_img,
                direction=direction,
                offset=offset,
                sig_width=sig_width,
                sig_height=sig_height,
            )
            if signed_pdf:
                report_attachment.write({"datas": signed_pdf})
            return True

    def _generate_pdf_report(self):
        """Generate PDF report for the record. Override in subclasses."""
        pass

    def _get_temporary_word(self):
        """Return the placeholder keyword used to locate the signature position."""
        return r"{{USER-SIGNATURE}}"

    def _get_attachment_report(self):
        """Return the report attachment for this record."""
        return self.report_attachment_id
