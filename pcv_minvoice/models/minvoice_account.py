from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..utils.minvoice_api_helper import MInvoiceAPI
from ..utils.common import notify_popup_operation, notify_rainbow_operation
from ..const import MINVOICE_GET_INVOICE_TEMPLATES_ENDPOINT


class MInvoiceTemplate(models.Model):
    _name = "minvoice.account"
    _description = "Tài khoản M-invoice"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "partner_id"

    partner_id = fields.Many2one(
        "res.partner", string="Thông tin tài khoản", required=True,
        tracking=True)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company, required=True)
    username = fields.Char(string="Tên tài khoản",
                           required=True, tracking=True)
    password = fields.Char(string="Mật khẩu", required=True, tracking=False, groups="base.group_system")
    production_host = fields.Char(
        string="Production Host", groups="base.group_system"
    )
    toggle_status = fields.Boolean(
        string="Toggle Status", default=False, copy=False)
    status = fields.Selection(
        [("inactive", "Không hoạt động"), ("active", "Đang hoạt động")],
        help="Kết nối với M-Invoice",
        default="inactive",
        compute="_compute_get_status",
        inverse="_inverse_set_status",
        tracking=True,
    )

    @api.depends('toggle_status')
    def _compute_get_status(self):
        for record in self:
            record.status = "active" if record.toggle_status else "inactive"

    def _inverse_set_status(self):
        for record in self:
            record.toggle_status = False if record.status == "inactive" else True

    @api.model
    def _get_invoice_templates_endpoint(self):
        endpoint = f"{MINVOICE_GET_INVOICE_TEMPLATES_ENDPOINT}"
        return endpoint

    def disconnect(self):
        self.ensure_one()
        self.sudo().write({"toggle_status": False})
        return notify_popup_operation("Ngắt kết nối thành công...")

    def reconnect(self):
        self.ensure_one()
        response = self._test_minvoice_connection()
        if response:
            if response.ok:
                self.sudo().write({"toggle_status": True})
                return notify_popup_operation("Kết nối thành công...")
            elif isinstance(response, dict):
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Thông báo!",
                        "message": response.get("message"),
                        "next": {"type": "ir.actions.act_window_close"},
                    },
                }
        else:
            return response

    def test_minvoice_connection(self):
        self.ensure_one()
        response = self._test_minvoice_connection()
        if isinstance(response, dict) and response.get('error'):
            raise ValidationError(
                response.get('message', 'Error')
            )
        if not response or not response.ok:
            raise ValidationError(
                _("Không thể xác thực kết nối! Vui lòng kiểm tra lại thông tin kết nối")
            )

        json_response = response.json()
        if json_response.get("token"):
            return notify_rainbow_operation()

        error_msg = json_response.get("error", "Không tìm thấy token!")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Thông báo!",
                "message": error_msg,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _test_minvoice_connection(self):
        self.ensure_one()
        minvoice_api = MInvoiceAPI(self)
        return minvoice_api.connect_with_credential()

    def _update_minvoice_template(self, data):
        new_templates = data["data"] or []
        to_create_templates, overlapped_templates = [], self.env["minvoice.template"]
        all_existed_template_codes = self.env["minvoice.template"].search(
            [("minvoice_account_id", "=", self.id)])

        for new_template in new_templates:
            template_type = str(new_template["lhdon"])
            overlapped_template = all_existed_template_codes.filtered(
                lambda r: r.code == template_type and r.invoice_series == new_template["value"]
            )
            if overlapped_template:
                overlapped_templates |= overlapped_template
            else:
                to_create_templates.append(
                    {
                        "code": template_type,
                        "minvoice_type": template_type,
                        "invoice_series": new_template["value"],
                        "minvoice_account_id": self.id,
                    }
                )

        to_update_templates = all_existed_template_codes - overlapped_templates
        if to_update_templates:
            to_update_templates.write({"active": False})

        if to_create_templates:
            self.env["minvoice.template"].create(to_create_templates)

    def action_update_minvoice_template(self):
        if self.status != "active":
            raise ValidationError(
                _("Tài khoản M-invoice hiện tại không hoạt động. Vui lòng kiểm tra và thử lại!"))
        try:
            minvoice_api = MInvoiceAPI(self)
            endpoint = self._get_invoice_templates_endpoint()
            res = minvoice_api.make_request('GET', endpoint)
            if res["ok"]:
                self._update_minvoice_template(res["data"])
                return notify_popup_operation("Mẫu hóa đơn điện tử đang được cập nhật...")
            else:
                raise ValidationError(
                    _(res["data"].get("data") or res["data"].get("message")))
        except Exception as e:
            raise ValidationError(
                _("Lỗi khi gửi yêu cầu tới M-invoice: %s", str(e))) from e

    def action_view_minvoice_template(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pcv_minvoice.action_view_minvoice_template")
        action["domain"] = [("minvoice_account_id", "=", self.id)]
        return action
