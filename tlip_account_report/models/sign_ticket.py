from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SignTicket(models.Model):
    _inherit = "sign.ticket"

    report_name = fields.Char(
        string="Report Name",
        help="Auto-filled when the ticket is created from an accounting report. "
             "Format: [Report Name] - [Period]",
        tracking=True, copy=False
    )

    @api.constrains("report_name", "state", "company_id", "document_type_id")
    def _check_duplicate_esign_ticket(self):
        super()._check_duplicate_esign_ticket()
        for rec in self:
            if rec.document_type_id.account_report_id and rec.report_name and rec.state != "cancelled":
                existing_ticket = self.env['account.report'].check_duplicate_esign_ticket(
                    rec.report_name, rec.company_id.id)
                if existing_ticket and existing_ticket.id != rec.id:
                    state = existing_ticket._get_selection_value("state")
                    raise UserError(
                        _("The report '%s' already has an associated sign ticket '%s' in state '%s'. ")
                        % (rec.report_name, existing_ticket.name, state)
                    )

    def _get_selection_value(self, field_name):
        field_dict = dict(self._fields[field_name].selection)
        value = getattr(self, field_name)
        return field_dict.get(value, '')
