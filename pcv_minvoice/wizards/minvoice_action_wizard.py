from datetime import datetime
import json
import uuid

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError

from ..const import (
    MINVOICE_SAVE_INVOICE_ENDPOINT,
    MINVOICE_SAVE_AND_SIGN_INVOICE_ENDPOINT,
    MINVOICE_SIGN_INVOICE_ENDPOINT,
    MINVOICE_ADJUST_INVOICE_ENDPOINT,
    MINVOICE_REPLACE_INVOICE_ENDPOINT,
    MINVOICE_CANCEL_INVOICE_ENDPOINT,
)
from ..utils.common import notify_popup_operation, notify_error
from ..utils.minvoice_helper import MInvoiceCaller
import logging
logger = logging.getLogger(__name__)


class MInvoiceActionWizard(models.TransientModel):
    """
    This wizard is used to perform action with MInvoice Invoice
    """

    _name = "minvoice.action.wizard"
    _inherit = ["minvoice.base"]
    _description = "MInvoice Action Wizard"

    minvoice_action = fields.Selection(
        [
            ("save", "Lưu HĐ"),
            ("publish", "Lưu và ký HĐ"),
            ("adjust", "Điều chỉnh HĐ"),
            ("replace", "Thay thế HĐ"),
            ("cancel", "Hủy HĐ điện tử"),
        ],
        string="Thực hiện",
        copy=False,
        default="save",
    )
    move_id = fields.Many2one("account.move")
    minvoice_account_id = fields.Many2one("minvoice.account", related="move_id.journal_id.minvoice_account_id")
    agreement_document = fields.Char(string="Văn bản thỏa thuận")
    agreement_date = fields.Date(string="Ngày thỏa thuận", default=datetime.now().replace(microsecond=0))
    cancel_reason = fields.Char(string="Lý do xóa bỏ")
    minvoice_print_file = fields.Binary(string="Draft Preview Invoice")
    minvoice_type = fields.Selection(related="minvoice_template_id.minvoice_type")
    can_update_minvoice = fields.Boolean(compute='_compute_can_update_minvoice')

    @api.constrains("minvoice_action")
    def check_minvoice_action(self):
        for record in self:
            if record.move_id.minvoice_publish_state == "unpublished" and \
                record.minvoice_action == "cancel":
                raise ValidationError(_("Không được phép điều chỉnh / thay thế / hủy hóa đơn chưa phát hành"))
            
    def _compute_can_update_minvoice(self):
        for record in self:
            record.can_update_minvoice = record.move_id.minvoice_state == 'created' and \
                record.move_id.minvoice_publish_state == "unpublished"

    @api.model
    def get_minvoice_template_code_selection(self, domain=None):
        if self._context.get('minvoice_account_id'):
            domain = [('minvoice_account_id', '=', self._context.get('minvoice_account_id'))]
        return super(MInvoiceActionWizard, self).get_minvoice_template_code_selection(domain)

    def _minvoice_action(self, minvoice_caller, endpoint):
        method = f"_minvoice_action_{self.minvoice_action}"
        if hasattr(self, method):
            return getattr(self, method)(minvoice_caller, endpoint)

    def _get_updated_data(self, res_data, **kwargs):
        minvoice_no = str(int(res_data["shdon"])) if res_data['shdon'] else None
        updated_data = {
            "minvoice_index": res_data["hoadon68_id"],
            "minvoice_no": minvoice_no,
            "minvoice_email": res_data.get("email", False),
        }
        return updated_data
    
    def _prepare_minvoice_items_vals(self):
        items = self.move_id.lines_to_publish_minvoice()            
        item_infos = []
        decimal_places = self.move_id.currency_id.decimal_places
        for index, item in enumerate(items, 1):
            qty = item.quantity
            price_unit = abs(item.price_unit)
            discount_amount = price_unit * (item.discount / 100) * qty
            line_info = {
                "tchat": 1,
                "stt_rec0": index,
                "inv_itemName": item.name,
                "inv_unitCode": item.product_uom_id.name or "",
                "inv_quantity": qty,
                "inv_unitPrice": price_unit,
                "inv_discountPercentage": item.discount,
                "inv_discountAmount": discount_amount,
                "inv_TotalAmountWithoutVat": round(item.price_subtotal, decimal_places),
                "ma_thue": str(int(item.tax_ids[:1].amount)),
                "inv_vatAmount": item.price_total - item.price_subtotal,
                "inv_TotalAmount": round(item.price_total, decimal_places)
            }
 
            if self.minvoice_action == "create" and item.move_id.move_type == 'out_refund':
                line_info.update({
                    'inv_unitPrice': line_info['inv_unitPrice'] * -1,
                    'inv_TotalAmountWithoutVat': round(line_info['inv_TotalAmountWithoutVat'] * -1, decimal_places),
                })

            item_infos.append(line_info)
        if len(items) == 2 and not items[1].product_uom_id:
            item_infos[0]['inv_vatAmount'] = self.move_id.amount_tax
            item_infos[0]['inv_TotalAmount'] = round(item_infos[0]['inv_TotalAmountWithoutVat'] + self.move_id.amount_tax, decimal_places)
        return item_infos
    
    def _prepare_minvoice_extra_vals(self):
        return {}

    def _minvoice_action_save(self, minvoice_caller, endpoint):
        try:
            for data in minvoice_caller.prepare():
                res = minvoice_caller.api.make_request('POST', endpoint, data=json.dumps(data))
                if 'ok' not in res:
                    return res
            
                if res["ok"]:
                    updated_data = self._get_updated_data(res["data"]["data"])
                    self.move_id.update_minvoice_data(minvoice_state="created", data=updated_data)
                    self.move_id.action_sync_tax_confirmation()
                    return notify_popup_operation("Hóa đơn đang được lưu...")
                else:
                    msg = res['data'].get('message')
                    return notify_error(f"Đã xảy ra lỗi khi lưu hoá đơn.\n{msg}")
        except Exception as e:
            raise ValidationError(_("Lỗi khi gửi yêu cầu tới M-invoice: %s.\nVui lòng liên hệ quản trị viên của M-invoice để kiểm tra.", str(e))) from e
        
    def _minvoice_action_publish(self, minvoice_caller, endpoint):
        try:
            for data in minvoice_caller.prepare():
                move_id = self.move_id
                if not move_id.minvoice_transaction_id:
                    # Avoid duplicate transaction id
                    move_id.write({"minvoice_transaction_id": f"{move_id.display_name}_{uuid.uuid4()}"})

                res = minvoice_caller.api.make_request('POST', endpoint, data=json.dumps(data))
                logger.info(f"Minvoice publish response: {res} {endpoint}")
                if 'ok' not in res:
                    return res

                if res["ok"]:
                    if self.move_id.minvoice_state == 'uncreated':
                        updated_data = self._get_updated_data(res["data"]["data"])
                        self.move_id.update_minvoice_data(
                            minvoice_state="created",
                            minvoice_publish_state="published",
                            data=updated_data)
                    else:
                        self.move_id.update_minvoice_data(minvoice_publish_state="published")
                    self.move_id.action_sync_tax_confirmation()
                    return notify_popup_operation("Hóa đơn đang được phát hành...")
                else:
                    msg = res['data'].get('message')
                    logger.info(f"Minvoice publish error message: {res}")
                    self.move_id.message_post(body=_(f"Lỗi khi phát hành hóa đơn điện tử: {msg}"))
                    return notify_error(f"Đã xảy ra lỗi khi ký hoá đơn.\n{msg}")
        except Exception as e:
            raise ValidationError(_("Lỗi khi gửi yêu cầu tới M-invoice: %s.\nVui lòng liên hệ quản trị viên của M-invoice để kiểm tra.", str(e))) from e

    def _minvoice_action_adjust(self, minvoice_caller, endpoint):
        try:
            for data in minvoice_caller.prepare():
                res = minvoice_caller.api.make_request('POST', endpoint, data=json.dumps(data))
                if 'ok' not in res:
                    return res
                
                if res["ok"]:
                    updated_data = self._get_updated_data(res["data"]["data"])
                    self.move_id.update_minvoice_data(
                        minvoice_state="adjusted",
                        minvoice_publish_state="published",
                        data=updated_data
                    )
                    return notify_popup_operation("Hóa đơn đang được điều chỉnh...")
                else:
                    msg = res['data'].get('message')
                    return notify_error(f"Đã xảy ra lỗi khi điều chỉnh hoá đơn.\n{msg}")
        except Exception as e:
            raise ValidationError(_("Lỗi khi gửi yêu cầu tới M-invoice: %s. Vui lòng liên hệ quản trị viên của M-invoice để kiểm tra.", str(e))) from e

    def _minvoice_action_replace(self, minvoice_caller, endpoint):
        try:
            for data in minvoice_caller.prepare():
                res = minvoice_caller.api.make_request('POST', endpoint, data=json.dumps(data))
                if 'ok' not in res:
                    return res
                
                if res["ok"]:
                    updated_data = self._get_updated_data(res["data"]["data"])
                    self.move_id.update_minvoice_data(
                        minvoice_state="replaced",
                        minvoice_publish_state="published",
                        data=updated_data
                    )
                    return notify_popup_operation("Hóa đơn đang được thay thế...")
                else:
                    msg = res['data'].get('message')
                    return notify_error(f"Đã xảy ra lỗi khi thay thế hoá đơn.\n{msg}")
        except Exception as e:
            raise ValidationError(_("Lỗi khi gửi yêu cầu tới M-invoice: %s. Vui lòng liên hệ quản trị viên của M-invoice để kiểm tra.", str(e))) from e

    def _minvoice_action_cancel(self, minvoice_caller, endpoint):
        try:
            for data in minvoice_caller.prepare():
                res = minvoice_caller.api.make_request('POST', endpoint, data=json.dumps(data))
                if 'ok' not in res:
                    return res
                
                if res["ok"]:
                    minvoice_no = self.move_id.minvoice_no
                    self.move_id.update_minvoice_data(
                        minvoice_state="uncreated",
                        minvoice_publish_state="unpublished",
                        data={
                            "minvoice_index": False,
                            "minvoice_no": False,
                            "minvoice_issued_date": False,
                            "minvoice_email": False,
                        },
                    )
                    self.move_id.message_post(body=_(f"Hóa đơn điện tử số {minvoice_no} đã bị huỷ."))
                    if self._context.get("cancel_minvoice"):
                        self.move_id.button_draft()
                    return notify_popup_operation("Hóa đơn đang được hủy...")
                else:
                    msg = res['data'].get('message')
                    return notify_error(f"Đã xảy ra lỗi khi huỷ hoá đơn.\n{msg}")
        except Exception as e:
            raise ValidationError(_("Lỗi khi gửi yêu cầu tới M-invoice: %s. Vui lòng liên hệ quản trị viên của M-invoice để kiểm tra.", str(e))) from e

    def button_do_action_minvoice(self):
        self.ensure_one()
        if self.minvoice_action in ["adjust", "replace"] and (
            self.minvoice_template_code != self.original_minvoice_template_code
            or self.minvoice_template_id != self.original_minvoice_template_id
        ):
            raise UserError(_("Hóa đơn gốc và hóa đơn điều chỉnh/thay thế phải cùng mẫu và ký hiệu."))

        if not self.minvoice_type:
            raise UserError(_("Vui lòng thiết lập loại hóa đơn của mẫu hóa đơn trước khi thực hiện yêu cầu!"))
        if self.move_id.minvoice_publish_state == 'published' and self.minvoice_action in ('save', 'publish'):
            raise UserError(_("Hoá đơn đã phát hành trên M-invoice"))
        
        minvoice_base_vals = self._get_minvoice_base_vals()
        self.move_id.write(minvoice_base_vals)

        minvoice_account = self._get_active_minvoice_account()
        minvoice_caller = MInvoiceCaller(minvoice_account, self)
        endpoint = self._get_minvoice_endpoint()
        return self._minvoice_action(minvoice_caller, endpoint)

    def button_send_minvoice_email(self):
        self.ensure_one()
        return self.move_id.action_send_minvoice_email()
    
    def button_update_minvoice(self):
        self.ensure_one()
        minvoice_account = self._get_active_minvoice_account()
        minvoice_caller = MInvoiceCaller(minvoice_account, self)
        endpoint = MINVOICE_SAVE_INVOICE_ENDPOINT
        return self._minvoice_action_save(minvoice_caller, endpoint)
    
    def button_delete_minvoice(self):
        self.ensure_one()
        return self.move_id.action_delete_unpulished_minvoice()

    def _get_active_minvoice_account(self):
        minvoice_account = self.move_id.journal_id.minvoice_account_id
        if minvoice_account.status != "active":
            raise ValidationError(_("Tài khoản M-invoice hiện tại không hoạt động. Vui lòng kiểm tra và thử lại!"))
        return minvoice_account

    def _get_minvoice_base_vals(self):
        self.ensure_one()
        return {
            name: field.convert_to_write(self[name], self) for name, field in self.env["minvoice.base"]._fields.items()
        }

    def _get_minvoice_endpoint(self):
        endpoint = False
        if self.minvoice_action == 'save':
            endpoint = MINVOICE_SAVE_INVOICE_ENDPOINT
        elif self.minvoice_action == 'publish':
            if self.move_id.minvoice_state != 'uncreated':
                endpoint = MINVOICE_SIGN_INVOICE_ENDPOINT
            else:
                endpoint = MINVOICE_SAVE_AND_SIGN_INVOICE_ENDPOINT
        elif self.minvoice_action == 'adjust':
            endpoint = MINVOICE_ADJUST_INVOICE_ENDPOINT
        elif self.minvoice_action =='replace':
            endpoint = MINVOICE_REPLACE_INVOICE_ENDPOINT
        elif self.minvoice_action == 'cancel':
            endpoint = MINVOICE_CANCEL_INVOICE_ENDPOINT

        return endpoint

    def _open_specific_minvoice_wizard_by_id(self, minvoice_id=None):
        return {
            "name": "Xuất hóa đơn điện tử ",
            "view_mode": "form",
            "view_id": self.env.ref("pcv_minvoice.minvoice_action_wizard_view_form").id,
            "view_type": "form",
            "res_model": "minvoice.action.wizard",
            "res_id": minvoice_id or self.id,
            "type": "ir.actions.act_window",
            "target": "new",
            "domain": "[]",
        }
