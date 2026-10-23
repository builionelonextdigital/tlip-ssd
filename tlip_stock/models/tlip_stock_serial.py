import base64
import qrcode
from io import BytesIO

from odoo import fields, models, _


class TlipStockSerial(models.Model):
    _name = 'tlip.stock.serial'
    _description = "Stock Serial Number"

    serial_number = fields.Integer(required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        index=True, required=True, readonly=True
    )
    package_id = fields.Many2one(
        'stock.quant.package',
        string='Asset Code',
        readonly=True
    )
    qr_code = fields.Binary(string="QR Code")
    quantity = fields.Integer(default=1)

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.product_id.default_code}_{(record.serial_number):03d}"

    def _generate_qr_code(self):
        for rec in self:
            qr = qrcode.QRCode(
                version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(rec.display_name)
            qr.make(fit=True)

            with BytesIO() as buffer:
                qr.make_image(fill_color="black", back_color="white").save(
                    buffer, format="PNG")
                rec.write({"qr_code": base64.b64encode(buffer.getvalue())})
