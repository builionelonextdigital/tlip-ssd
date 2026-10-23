import base64
import uuid
import qrcode
from io import BytesIO

from odoo import models, fields, _


class NonLandPlotItem(models.Model):
    _inherit = 'product.template'

    type = fields.Selection(
        string="Product Type",
        selection=[
            ('consu', "Goods"),
            ('service', "Service"),
        ]
    )
    model = fields.Char('Model')
    manufacturer_id = fields.Many2one('product.manufacturer', 'Manufacturer')
    specification_ids = fields.One2many('product.specification', 'product_template_id', 'Product Template')
    qr_code = fields.Binary(string="QR Code")

    def generate_qr_code(self):
        self.ensure_one()

        random_uuid = str(uuid.uuid4())
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(random_uuid)
        qr.make(fit=True)

        with BytesIO() as buffer:
            qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
            self.qr_code = base64.b64encode(buffer.getvalue())