import base64
import io
import re
import zipfile

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountReport(models.Model):
    _inherit = "account.report"

    def _get_esign_period_string(self, options):
        """
        Reuse account.report.format_date() to extract a period string from
        the current report options (e.g. '10/2026' or 'Jan 2026').
        Falls back to date_to formatted as MM/YYYY if format_date fails.
        """
        try:
            return self.format_date(options)
        except Exception:
            date_to = options.get("date", {}).get("date_to", "")
            if date_to:
                from datetime import datetime
                try:
                    return datetime.strptime(date_to, "%Y-%m-%d").strftime("%m/%Y")
                except ValueError:
                    return date_to
            return ""

    @api.model
    def check_duplicate_esign_ticket(self, report_name, company_id=None):
        company_id = company_id or self.env.company.id
        return self.env["sign.ticket"].search([
            ("report_name", "=", report_name),
            ("company_id", "=", company_id),
            ("state", "not in", ("cancelled", "approved", "rejected")),
        ], limit=1)

    def _get_pdf_button_and_record(self, options):
        pdf_button = None
        for option in options.get("buttons", []):
            if option.get("file_export_type") == "PDF":
                pdf_button = option
                break

        if not pdf_button:
            return None, None

        method_name = pdf_button.get("action_param") or pdf_button.get("action")
        if not method_name:
            return pdf_button, None

        custom_handler_model = self._get_custom_handler_model()
        if custom_handler_model:
            custom_handler = self.env[custom_handler_model].sudo()
            if hasattr(custom_handler, method_name):
                return pdf_button, custom_handler

        return pdf_button, self

    def _extract_file_content_from_pdf_action(self, result, period_string):
        file_content = result.get("file_content")
        if file_content:
            file_name = f"{result.get('file_name')} - {period_string}.pdf"
            return [(file_name, file_content)]

        attachment_url = result.get("url") or result.get("attachment_url")
        attachment_id = None
        if attachment_url:
            match = re.search(r"/web/content/(\d+)", attachment_url)
            if match:
                attachment_id = int(match.group(1))

        attachment_id = attachment_id or result.get("attachment_id")
        attachment = self.env["ir.attachment"].sudo().browse(attachment_id).exists()
        if not attachment:
            raise UserError(_("Failed to resolve attachment from report URL."))

        attachment_content = base64.b64decode(attachment.datas or b"")
        if attachment.mimetype == "application/zip" or (attachment.name or "").lower().endswith(".zip"):
            file_contents = []
            with zipfile.ZipFile(io.BytesIO(attachment_content)) as zip_file:
                for zip_info in zip_file.infolist():
                    if zip_info.is_dir():
                        continue
                    file_name = f"{zip_info.filename} - {period_string}.pdf"
                    file_contents.append((file_name, zip_file.read(zip_info.filename)))
            return file_contents

        return [(f"{attachment.name} - {period_string}.pdf" if attachment.name else f"report - {period_string}.pdf", attachment_content)]

    def _prepare_sign_ticket_vals(self, options):
        variants = options.get('available_variants') or []
        report_id = variants[0].get('id') if variants else False
        report = self.env['account.report'].browse(report_id)
        document_type = self.env['sign.document.type'].search(
            [('account_report_id', '=', report_id)], limit=1)
        report_label = report.name or _("Account Report")
        period = self._get_esign_period_string(options)
        report_name = f"{report.name} - {period}"

        pdf_button, record = self._get_pdf_button_and_record(options)
        if not pdf_button:
            raise UserError(_("Failed to generate PDF for '%s'.") % report_label)

        method_name = pdf_button.get("action_param") or pdf_button.get("action")
        if not method_name:
            raise UserError(_("Failed to generate PDF for '%s'.") % report_label)

        result = getattr(record, method_name)(options)
        file_contents = self._extract_file_content_from_pdf_action(result, period)
        if not file_contents:
            raise UserError(_("Failed to generate PDF for '%s'.") % report_label)

        return report_name, {
            "report_name": report_name,
            "signing_type": "mysign",
            "company_id": self.env.company.id,
            "document_type_id": document_type.id if document_type else False,
            "sign_document_ids": [
                (0, 0, {
                    "file": base64.b64encode(file_content),
                    "filename": filename,
                })
                for filename, file_content in file_contents
            ],
        }

    def action_request_esign(self, options):
        self.ensure_one()
        if len(options.get("companies", [])) > 1:
            raise UserError(_("E-Sign is only supported for single-company reports."))

        variants = options.get('available_variants') or []
        report_id = variants[0].get('id') if variants else False
        if not self.env['account.report'].browse(report_id):
            return

        report_name, vals = self._prepare_sign_ticket_vals(options)
        ticket = self.check_duplicate_esign_ticket(report_name)
        if not ticket:
            ticket = self.env["sign.ticket"].create(vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "sign.ticket",
            "res_id": ticket.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "current",
        }

    ####################################################
    # OPTIONS: OVERRIDE BUTTONS
    ####################################################
    def _init_options_buttons(self, options, previous_options):
        super()._init_options_buttons(options, previous_options)

        variants = options.get('available_variants') or []
        report_id = variants[0].get('id') if variants else False
        if not report_id:
            return

        if not self.env.user.has_group('pcv_sign_ticket.group_sign_ticket_user'):
            return

        document_type = self.env['sign.document.type'].search(
            [('account_report_id', '=', report_id)], limit=1
        )
        if document_type:
            options["buttons"].extend([
                {'name': _('Request E-Sign'), 'sequence': 30, 'action': 'action_request_esign', 'branch_allowed': True, 'always_show': True},
            ])
