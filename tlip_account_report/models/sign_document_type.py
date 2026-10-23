from odoo import api, fields, models


class SignDocumentType(models.Model):
    _inherit = "sign.document.type"

    account_report_id = fields.Many2one(
        comodel_name="account.report",
        string="Account Report",
        ondelete="set null",
    )
    model_name = fields.Char(related="model_id.model", string="Model Name")

    @api.onchange('account_report_id')
    def _onchange_account_report_id(self):
        if self.account_report_id:
            self.use_cell_positioning = True
            self.placeholder_text = r"{{USER-SIGNATURE}}"

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id.model != 'account.report':
            self.account_report_id = False
