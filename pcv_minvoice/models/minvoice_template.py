from odoo import models, fields, api, _
from ..const import MINVOICE_TYPE_SELECTION, PAYMENT_METHOD_SELECTION


class MInvoiceTemplate(models.Model):
    _name = "minvoice.template"
    _description = "Electronic Invoice Template"
    _rec_name = "invoice_series"

    minvoice_type = fields.Selection(
        selection=MINVOICE_TYPE_SELECTION,
        string="Tên loại hóa đơn")
    code = fields.Char(string="Ký hiệu loại hóa đơn")
    invoice_series = fields.Char(string="Ký hiệu hóa đơn")
    active = fields.Boolean(string="Trạng thái", default=True)
    payment_method = fields.Selection(
        selection=PAYMENT_METHOD_SELECTION,
        string="Hình thức thanh toán")
    currency_id = fields.Many2one('res.currency', string='Loại tiền',
                                  default=lambda self: self.env.company.currency_id)
    journal_ids = fields.Many2many("account.journal", string="Sổ nhật ký")
    minvoice_account_id = fields.Many2one(
        'minvoice.account', string='Tài khoản')
    company_id = fields.Many2one('res.company', related='minvoice_account_id.company_id', store=True)
