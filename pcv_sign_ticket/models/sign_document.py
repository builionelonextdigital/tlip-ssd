import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SignDocument(models.Model):
    _name = "sign.document"
    _description = "Sign Document"
    _rec_name = "filename"

    ticket_id = fields.Many2one(
        comodel_name="sign.ticket",
        string="Sign Ticket",
        required=True,
        ondelete="cascade"
    )
    file = fields.Binary("Document", attachment=True, required=True)
    filename = fields.Char("Filename")
    original_file = fields.Binary("Original Document", attachment=True, readonly=True)
    is_pdf = fields.Boolean(compute="_compute_is_pdf")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("file") and not vals.get("original_file"):
                vals["original_file"] = vals["file"]
        return super().create(vals_list)

    def write(self, vals):
        if "file" in vals:
            draft = self.filtered(lambda r: r.ticket_id.state == "draft")
            non_draft = self - draft
            if draft:
                super(SignDocument, draft).write({**vals, "original_file": vals["file"]})
            if non_draft:
                super(SignDocument, non_draft).write(vals)
            return True
        return super().write(vals)

    def _clear_original_file(self):
        self.write({"original_file": False})

    def _restore_original(self):
        """Restore file to the original uploaded version."""
        for record in self.filtered("original_file"):
            record.file = record.original_file

    @api.depends("filename")
    def _compute_is_pdf(self):
        for record in self:
            record.is_pdf = bool(record.filename and record.filename.endswith(".pdf"))

    def _get_pdf_bytes(self):
        """Return the decoded PDF content as bytes."""
        self.ensure_one()
        if not self.is_pdf:
            raise UserError(_("Only PDF documents are supported."))
        return base64.decodebytes(self.file)
