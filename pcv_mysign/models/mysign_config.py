from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.addons.pcv_mysign.utils.common import BASE_URL, show_notification


class MysignConfig(models.Model):
    _name = "mysign.config"
    _description = "Viettel MySign Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True, tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    url_api = fields.Char(string="API URL", required=True, default=BASE_URL, tracking=True)
    tsa_url = fields.Char(
        string="TSA URL",
        help="RFC 3161 timestamp authority URL. When set, an embedded trusted timestamp "
             "replaces the local-clock warning in PDF readers.",
        tracking=True,
    )
    client_id = fields.Char(string="Client ID", required=True, tracking=True)
    client_secret = fields.Char(string="Client Secret", required=True)
    profile_id = fields.Char(string="Profile ID", required=True, tracking=True)
    mysign_account_ids = fields.One2many(
        comodel_name="mysign.account",
        inverse_name="config_id",
        string="Sessions",
    )
    active_account_id = fields.Many2one(
        comodel_name="mysign.account",
        string="Active Session",
        compute="_compute_active_account_id",
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    def _compute_active_account_id(self):
        for rec in self:
            valid = rec.mysign_account_ids.filtered(lambda a: a.state == "connected")
            rec.active_account_id = valid[:1]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_token_valid(self):
        self.ensure_one()
        return bool(self.active_account_id)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def test_mysign_connection(self):
        self.ensure_one()
        if not self.mysign_account_ids:
            raise UserError(_("No account configured. Please add at least one account first."))
        failed = []
        for account in self.mysign_account_ids:
            try:
                account.action_login()
            except Exception:
                failed.append(account.code)
        total = len(self.mysign_account_ids)
        if failed:
            return show_notification(
                _("Connection Test Done"),
                _("%d/%d account(s) failed to connect: %s") % (len(failed), total, ", ".join(failed)),
            )
        return show_notification(
            _("Connection Test Done"),
            _("All %d account(s) connected successfully.") % total,
        )

    def disconnect(self):
        self.ensure_one()
        self.write({"active": False})
        for account in self.mysign_account_ids:
            account.disconnect()

        return show_notification(_("Disconnected"), _("The MySign has been disconnected."))

    def reconnect(self):
        self.ensure_one()
        self.write({"active": True})

        return show_notification(_("Reconnected"), _("The MySign has been reconnected."))
