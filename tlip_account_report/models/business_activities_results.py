from odoo import _, models


class BusinessActivitiesResults(models.Model):
    _name = "business.activities.results"
    _inherit = ["business.activities.results", "sign.ticket.mixin"]

    def _get_sign_ticket_report_filename(self, report):
        self.ensure_one()
        filename = self.name or _("Business Activities Results")
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"
        return filename
