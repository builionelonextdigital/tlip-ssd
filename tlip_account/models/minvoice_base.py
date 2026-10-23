from odoo import models, fields

PAYMENT_METHOD_SELECTION = [
    ('TM/CK', 'TM/CK'),
    ('cash', 'Tiền mặt/Cash'),
    ('transfer', 'Chuyển khoản/Bank Transfer')
]


class MInvoiceBase(models.AbstractModel):
    _inherit = "minvoice.base"

    minvoice_template_payment_method = fields.Selection(
        selection=PAYMENT_METHOD_SELECTION,
    )

    def _get_minvoice_template_vals(self, template_id, default_text=""):
        result = super()._get_minvoice_template_vals(
            template_id=template_id, default_text=default_text
        )
        result.update(
            {
                f"{default_text}minvoice_template_payment_method": self.minvoice_template_payment_method,
            }
        )
        return result


class MInvoiceTemplate(models.Model):
    _inherit = "minvoice.template"

    payment_method = fields.Selection(
        selection=PAYMENT_METHOD_SELECTION
    )
