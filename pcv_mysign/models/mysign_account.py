from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.addons.pcv_mysign.utils.common import get_error_description, show_notification
from odoo.addons.pcv_mysign.utils.mysign_api_helper import MysignAPI, MysignAPIError


class MysignAccount(models.Model):
    _name = "mysign.account"
    _description = "Viettel MySign Account Session"
    _order = "create_date desc"

    config_id = fields.Many2one(
        comodel_name="mysign.config",
        string="Configuration",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        related="config_id.company_id",
        store=True,
        readonly=True,
    )
    code = fields.Char(string="Code", required=True, tracking=True)
    state = fields.Selection(
        selection=[
            ("connected", "Connected"),
            ("idle", "Idle"),
        ],
        string="Status",
        default="idle",
        readonly=True,
    )
    access_token = fields.Char(string="Access Token", readonly=True)
    refresh_token = fields.Char(string="Refresh Token", readonly=True)
    token_type = fields.Char(string="Token Type", readonly=True)
    expires_in = fields.Char(string="Expires In (seconds)", readonly=True)
    token_expiry = fields.Datetime(string="Token Expiry", readonly=True)
    last_authenticated_datetime = fields.Datetime(string="Last Authenticated Datetime", readonly=True)

    def _compute_display_name(self):
        for record in self:
            record.display_name = "%s (%s)" % (record.code, record.company_id.name)

    @api.model
    def _get_mysign_account(self, user, company):
        account = user.mysign_account_ids.filtered(lambda a: a.company_id == company)[:1]
        if account:
            return account

        company_account = company.mysign_config_ids.active_account_id
        return company_account

    def _get_api(self):
        self.ensure_one()
        return MysignAPI(self.config_id, self)

    def _ensure_active(self):
        self.ensure_one()
        if self._is_token_expired():
            self.action_login()

    def _is_token_expired(self):
        self.ensure_one()
        if not self.token_expiry:
            return True
        return datetime.now() >= self.token_expiry

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_open_form(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "mysign.account",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_login(self):
        self.ensure_one()
        self = self.sudo()
        try:
            api = self._get_api()
            status_code, data = api.login(user_id=self.code)
        except MysignAPIError as e:
            raise UserError(str(e))

        if status_code == 200:
            expires_in = int(data.get("expires_in", 3600))
            self.write({
                "state": "connected",
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token", ""),
                "token_type": data.get("token_type", "Bearer"),
                "expires_in": data.get("expires_in"),
                "token_expiry": fields.Datetime.add(fields.Datetime.now(), seconds=expires_in),
            })
            return show_notification(_("Login Successful"), _("Access token retrieved successfully."))
        error_code = data.get("error", "")
        error_desc = get_error_description(error_code) or data.get("error_description", _("Unknown error"))
        raise UserError(_("[%s] %s") % (error_code, error_desc))

    def action_check_token(self):
        self.ensure_one()
        if self._is_token_expired():
            return self.action_login()
        return show_notification(
            _("Token Valid"),
            _("Access token is still valid until %s.") % self.token_expiry,
        )

    def disconnect(self):
        for record in self:
            record.write({
                "state": "idle",
                "access_token": "",
                "refresh_token": "",
                "token_type": "",
                "expires_in": "",
                "token_expiry": None,
            })
