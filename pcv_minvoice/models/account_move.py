from datetime import datetime
import json
import base64
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..const import (
    MINVOICE_VIEW_INVOICE_PRINT_ENDPOINT,
    MINVOICE_SEND_EMAIL_ENDPOINT,
    MINVOICE_SAVE_INVOICE_ENDPOINT,
    MINVOICE_GET_INVOICE_STATUS_ENDPOINT,
)
from ..utils.minvoice_api_helper import MInvoiceAPI
from ..utils.common import notify_popup_operation, notify_error, notify_warning

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "minvoice.base"]

    minvoice_state = fields.Selection(
        [
            ("uncreated", "Chưa tạo hoá đơn"),
            ("created", "Đã tạo hoá đơn"),
            ("adjusted", "Hóa đơn điều chỉnh"),
            ("be_adjusted", "Hóa đơn bị điều chỉnh"),
            ("replaced", "Hóa đơn thay thế"),
            ("be_replaced", "Hóa đơn bị thay thế"),
        ],
        default="uncreated",
        copy=False,
        string="M-invoice Type",
    )
    minvoice_publish_state = fields.Selection(
        [
            ("unpublished", "Chờ phát hành"),
            ("published", "Đã phát hành"),
        ],
        default="unpublished",
        copy=False,
        string="M-invoice Status",
    )
    minvoice_no = fields.Char(string="Invoice Number", copy=False)
    minvoice_email = fields.Char(string="M-invoice Email", copy=False)
    minvoice_index = fields.Char(
        string="M-invoice ID",
        help="Unique, to identify corresponding M-invoice",
        copy=False,
    )
    minvoice_transaction_id = fields.Char(
        string="M-invoice Transaction ID",
        copy=False,
    )
    minvoice_account_id = fields.Many2one(
        'minvoice.account', related='journal_id.minvoice_account_id')

    tax_confirmation_status = fields.Selection([
        ('pending', 'Chờ xác nhận từ CQT'),
        ('success', 'Xác nhận thành công từ CQT'),
        ('rejected', 'Bị từ chối bởi CQT'),
    ], string='Tình trạng hóa đơn', copy=False)
    tax_note_error = fields.Text(string='Mã lỗi CQT', copy=False)
    tax_macqt = fields.Char(string='Mã CQT', copy=False)
    tax_lookup_code = fields.Char(string='Mã tra cứu', copy=False)
    tax_reference = fields.Char(string='Mã tra cứu', copy=False)
    tax_response_data = fields.Text(string='Phản hồi CQT', copy=False)
    minvoice_signing_date = fields.Datetime(string='Ngày ký M-invoice', copy=False)
    minvoice_signing_user = fields.Many2one('res.users', string='Người ký M-invoice', copy=False)

    def action_sync_tax_confirmation(self):
        """Button handler: Sync tax confirmation from M-Invoice"""
        self.ensure_one()
        return self._sync_tax_confirmation_from_minvoice()

    def _sync_tax_confirmation_from_minvoice(self):
        """Core sync logic: Call M-Invoice API and update tax confirmation fields"""
        self.ensure_one()
        minvoice_account = self._get_active_minvoice_account()
        minvoice_api = MInvoiceAPI(minvoice_account)
        params = {'id': self.minvoice_index}
        res = minvoice_api.make_request('GET', MINVOICE_GET_INVOICE_STATUS_ENDPOINT, params=params)

        # Network/request error — make_request returns an error notification dict
        if 'ok' not in res:
            return res

        if not res['ok']:
            data = res.get('data', {})
            error_msg = data.get('message') or data.get('data') or _("Lỗi không xác định từ M-Invoice")
            return notify_error(_("Lỗi M-Invoice: %s", error_msg))

        data = res.get('data', {})
        invoice_data = data.get('data') or {}
        if isinstance(invoice_data, list):
            invoice_data = invoice_data[0] if invoice_data else {}

        is_success = invoice_data.get('is_success')
        signing_date = invoice_data.get('nky')

        status = self._map_minvoice_tinh_trang_to_status(is_success)
        signing_date = self._map_minvoice_nky_to_signing_date(invoice_data.get('nky'))
        self.write({
            'tax_confirmation_status': status,
            'tax_note_error': invoice_data.get('note_error', ''),
            'tax_macqt': invoice_data.get('macqt', ''),
            'tax_lookup_code': invoice_data.get('sbmat', ''),
            'minvoice_signing_date': signing_date,
            'minvoice_signing_user': invoice_data.get('nky'),
            'tax_response_data': invoice_data.get('phanHoiCQT', ''),
        })

        if status == 'success':
            return notify_popup_operation(_("Đồng bộ xác nhận thuế thành công!"))
        elif status == 'rejected':
            return notify_error(_("Cơ quan thuế đã từ chối hóa đơn này."))
        else:
            return notify_warning(_("Cơ quan thuế chưa trả kết quả, vui lòng thử lại sau."))

    def _map_minvoice_tinh_trang_to_status(self, is_success):
        """Map is_success value to tax_confirmation_status.
        is_success=1 → success, is_success=0 → rejected
        """
        if is_success == 1 or is_success is True:
            return 'success'
        elif is_success == 0 or is_success is False:
            return 'rejected'
        else:
            return 'pending'

    def _map_minvoice_nky_to_signing_date(self, nky, format_string="%Y-%m-%dT%H:%M:%S.%f"):
        """Convert nky value from M-Invoice API to a datetime object"""
        if not nky:
            return False
        try:
            return datetime.strptime(nky, format_string)
        except ValueError:
            _logger.warning("Failed to parse signing date from M-Invoice: %s", nky)
            return False

    @api.model
    def _cron_sync_tax_confirmation(self):
        """Cron: Auto-sync tax confirmation for published invoices still pending"""
        moves = self.search([
            ('move_type', '=', 'out_invoice'),
            ('minvoice_publish_state', '=', 'published'),
            ('minvoice_index', '!=', False),
            ('tax_confirmation_status', 'in', ('pending', False)),
        ])
        for move in moves:
            try:
                move._sync_tax_confirmation_from_minvoice()
            except Exception as e:
                _logger.error("Error syncing tax confirmation for move %s: %s", move.name, str(e))

    @api.model
    def get_minvoice_template_code_selection(self, domain=None):
        if self._context.get('minvoice_account_id'):
            domain = [('minvoice_account_id', '=',
                       self._context.get('minvoice_account_id'))]
        return super(AccountMove, self).get_minvoice_template_code_selection(domain)

    @api.model
    def _get_view_minvoice_endpoint(self):
        endpoint = f"{MINVOICE_VIEW_INVOICE_PRINT_ENDPOINT}"
        return endpoint

    @api.model
    def _get_send_email_minvoice_endpoint(self):
        endpoint = f"{MINVOICE_SEND_EMAIL_ENDPOINT}"
        return endpoint
    
    @api.model
    def _get_delete_minvoice_endpoint(self):
        endpoint = f"{MINVOICE_SAVE_INVOICE_ENDPOINT}"
        return endpoint

    @api.model
    def _action_send_minvoice_email(self, minvoice_account, data):
        """
        Send M-invoice email for a specific M-invoice account.

        :param minvoice_account: M-invoice account
        :param data: Data to be sent in the request
        :return: Response from the M-invoice API
        """
        minvoice_api = MInvoiceAPI(minvoice_account)
        endpoint = self._get_send_email_minvoice_endpoint()
        res = minvoice_api.make_request('POST', endpoint, data=json.dumps(data))
        return res
    
    @api.model
    def _action_delete_minvoice(self, minvoice_account, data):
        minvoice_api = MInvoiceAPI(minvoice_account)
        endpoint = self._get_delete_minvoice_endpoint()
        res = minvoice_api.make_request('POST', endpoint, data=json.dumps(data))
        return res

    def update_minvoice_data(self, minvoice_state=None, minvoice_publish_state=None, data=None):
        vals = {}
        if minvoice_state:
            vals["minvoice_state"] = minvoice_state
        if minvoice_publish_state:
            vals["minvoice_publish_state"] = minvoice_publish_state
        if data:
            vals.update(data)
        if vals:
            self.write(vals)

        if minvoice_state == "replaced":
            self.original_invoice_id.write(
                {"state": "cancel", "minvoice_state": "be_replaced"}
            )
        elif minvoice_state == "adjusted":
            self.original_invoice_id.write({"minvoice_state": "be_adjusted"})

    def button_open_minvoice_wizard(self):
        self.ensure_one()

        vals = {f'{name}': field.convert_to_write(self[name], self)
                for name, field in self.env['minvoice.base']._fields.items()}
        vals.update({
            'move_id': self.id,
            'minvoice_issued_date': self.minvoice_issued_date or datetime.now().replace(microsecond=0)
        })

        if not self.minvoice_template_id and self.journal_id:
            template_id = self.env['minvoice.template'].search(
                [('journal_ids', 'in', self.journal_id.id)], limit=1)
            vals.update({
                'minvoice_template_id': template_id.id
            })
            vals.update(self._get_minvoice_template_vals(
                template_id=template_id, default_text=""))

        wizard = self.env['minvoice.action.wizard'].create(vals)
        return {
            'name': 'Xuất hóa đơn điện tử ',
            'view_mode': 'form',
            'view_id': self.env.ref('pcv_minvoice.minvoice_action_wizard_view_form').id,
            'view_type': 'form',
            'res_model': 'minvoice.action.wizard',
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': '[]',
            'context': dict(self.env.context) or {}
        }

    def _prepare_minvoice_wizard_vals(self):
        vals = {f'default_{name}': field.convert_to_write(self[name], self)
                for name, field in self.env['minvoice.base']._fields.items()}

        vals.update({
            'default_move_id': self.id,
            # If invoice has value minvoice_issued_date -> do not update, because minvoice_issued_date will be used to cancel M-invoice
            'default_minvoice_issued_date': self.minvoice_issued_date or datetime.now().replace(microsecond=0)
        })

        if not self.minvoice_template_id and self.journal_id:
            template_id = self.env['minvoice.template'].search(
                [('journal_ids', 'in', self.journal_id.id)], limit=1)
            vals.update({'default_minvoice_template_id': template_id.id})
            vals.update(self._get_minvoice_template_vals(
                template_id=template_id, default_text="default_"))

        return vals
    
    def lines_to_publish_minvoice(self):
        return self.invoice_line_ids.filtered(lambda line: line.display_type == 'product')

    def _get_active_minvoice_account(self):
        self.ensure_one()
        minvoice_account = self.journal_id.minvoice_account_id
        if minvoice_account.status != "active":
            raise UserError(
                _("Tài khoản M-invoice hiện tại không hoạt động. Vui lòng kiểm tra và thử lại!"))
        return minvoice_account

    def _prepare_data_to_send_email_minvoice(self):
        send_email_data = []
        for record in self:
            send_email_data.append({
                'id': record.minvoice_index,
                "nguoi_nhan": record.minvoice_email
            })
            
        return {
            "id": send_email_data,
            "type": "Gửi hóa đơn"
        }
    
    def _prepare_data_to_delete_minvoice(self):
        data = []
        for record in self:
            vals = {
                'inv_invoiceSeries': record.minvoice_template_id.invoice_series
            }
            if record.minvoice_no:
                vals.update({'inv_invoiceNumber': int(record.minvoice_no)})
            else:
                vals.update({'inv_InvoiceAuth_id': record.minvoice_index})

            data.append(vals)
            
        return {
            "editmode": 3,
            "data": data
        }

    def action_view_minvoice(self):
        self.ensure_one()
        if self.minvoice_state == 'unpublished':
            raise UserError(
                _("Hóa đơn này chưa được phát hành. Vui lòng phát hành trước khi xem."))
        
        minvoice_account = self._get_active_minvoice_account()
        try:
            minvoice_api = MInvoiceAPI(minvoice_account)
            endpoint = self._get_view_minvoice_endpoint()
            params = {
                "id": self.minvoice_index,
            }
            res = minvoice_api.make_request('GET', endpoint, params=params, raw_response=True)
            if 'ok' not in res:
                return res

            if res["ok"]:
                vals = {f'{name}': field.convert_to_write(self[name], self)
                    for name, field in self.env['minvoice.base']._fields.items()}
                vals.update({
                    "move_id": self.id,
                    "minvoice_print_file": base64.b64encode(res['data']),
                })
                exported_minvoice = self.env["minvoice.action.wizard"].create(vals)
                return {
                    "name": "Xem hóa đơn điện tử đã phát hành",
                    "view_mode": "form",
                    "view_id": self.env.ref("pcv_minvoice.minvoice_action_wizard_view_exported_einvoice").id,
                    "view_type": "form",
                    "res_model": "minvoice.action.wizard",
                    "res_id": exported_minvoice.id,
                    "type": "ir.actions.act_window",
                    "target": "new",
                }
            else:
                raise UserError(
                    _(res["data"].get("data") or res["data"].get("message")))
        except Exception as e:
            raise UserError(
                _("Lỗi khi gửi yêu cầu tới M-invoice: %s", str(e))) from e
        
    def action_delete_unpulished_minvoice(self, minvoice_account=None, data=None):
        self.ensure_one()
        if self.minvoice_state == 'uncreated':
            raise UserError(
                _("Hóa đơn này chưa được tạo trên M-invoice."))
        if self.minvoice_publish_state != 'unpublished':
            raise UserError(_("Không thể xoá hoá đơn đã phát hành."))

        minvoice_account = minvoice_account or self._get_active_minvoice_account()
        try:
            data = self._prepare_data_to_delete_minvoice()
            res = self._action_delete_minvoice(minvoice_account, data)
            if 'ok' not in res:
                return res
            
            if res["ok"]:
                self.write({
                    'minvoice_state': 'uncreated',
                    'minvoice_index': False,
                    'minvoice_no': False,
                    'minvoice_issued_date': False
                })
                return notify_popup_operation("Huỷ HĐ nháp thành công")
            else:
                msg = res['data'].get('message')
                return notify_error(f"Đã xảy ra lỗi khi xoá hoá đơn.\n{msg}")
        except Exception as e:
            raise UserError(
                _("Lỗi khi gửi yêu cầu tới M-invoice: %s", str(e))) from e

    def action_send_minvoice_email(self, minvoice_account=None, data=None):
        self.ensure_one()
        minvoice_account = minvoice_account or self._get_active_minvoice_account()
        try:
            if not self.minvoice_email:
                raise UserError(
                    _("Hóa đơn %s không có dữ liệu M-invoice Email", self.name))
            data = self._prepare_data_to_send_email_minvoice()
            res = self._action_send_minvoice_email(minvoice_account, data)
            if 'ok' not in res:
                return res
            
            if res["ok"]:
                return notify_popup_operation("Email đang được gửi từ M-invoice tới khách hàng...")
            else:
                msg = res['data'].get('message')
                return notify_error(f"Đã xảy ra lỗi khi gửi mail.\n{msg}")
        except Exception as e:
            raise UserError(
                _("Lỗi khi gửi yêu cầu tới M-invoice: %s", str(e))) from e
        
    def action_send_minvoice_emails(self):
        """
        Action to send M-invoice emails for multiple transactions.

        :return: Notification after sending emails
        """

        record_missing_emails = self.filtered(lambda r: not r.minvoice_email)
        record_inactive_accounts = self.filtered(lambda r: not (r.journal_id.minvoice_account_id and r.journal_id.minvoice_account_id.status == "active"))

        if record_missing_emails or record_inactive_accounts:
            errors = []
            if record_missing_emails:
                errors.append(f"Hóa đơn thiếu M-Invoice email: {', '.join(record_missing_emails)}")
            if record_inactive_accounts:
                errors.append(f"Tài khoản M-Invoice của các hoá đơn hiện tại không hoạt động: {', '.join(record_inactive_accounts)}")
            raise UserError(_("\n".join(errors)))
        
        records_by_account = {}
        for record in self:
            account = record.journal_id.minvoice_account_id
            if account not in records_by_account:
                records_by_account[account] = self.browse()
            records_by_account[account] |= record

        failed_accounts = []
        for account, records in records_by_account.items():
            try:
                data = records._prepare_data_to_send_email_minvoice()
                res = self._action_send_minvoice_email(account, data)
                
                if not res.get("ok"):
                    error = (res.get("data", {}).get("data") or 
                            res.get("data", {}).get("message") or 
                            "Lỗi không xác định")
                    failed_accounts.append(f"{account.name}: {error}")
                    
            except Exception as e:
                failed_accounts.append(f"{account.name}: {str(e)}")
        
        if failed_accounts:
            raise UserError(
                _("Gửi email thất bại:\n%s") % "\n".join(failed_accounts)
            )
        
        return notify_popup_operation(
            f"Đã gửi yêu cầu email cho {len(self)} hóa đơn..." if len(self) > 1
            else "Email đang được gửi từ M-invoice..."
        )

    def button_reset_to_draft_minvoice(self):
        if self.minvoice_publish_state != 'published':
            raise UserError(_("HĐ đã được ký trên M-invoice. Không thể đưa về dự thảo"))
        
        return {
            "name": "Xác nhận hủy hóa đơn điện tử",
            "view_mode": "form",
            "view_id": self.env.ref("pcv_minvoice.minvoice_cancelled_wizard_view_form").id,
            "view_type": "form",
            "res_model": "minvoice.action.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {**self._prepare_minvoice_wizard_vals(), "default_minvoice_action": "cancel"},
        }
