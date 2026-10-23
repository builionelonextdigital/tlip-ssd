from odoo import _, models


class AccountingBalanceSheetReport(models.Model):
    _name = "accounting.balance.sheet.report"
    _inherit = ["accounting.balance.sheet.report", "sign.ticket.mixin"]

    def _get_sign_ticket_report_filename(self, report):
        self.ensure_one()
        report_name = self.display_name or report.name or _("Accounting Balance Sheet")
        if not report_name.lower().endswith(".pdf"):
            report_name = f"{report_name}.pdf"
        return report_name
