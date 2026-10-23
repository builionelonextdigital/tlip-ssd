from odoo import api, fields, models
from odoo.exceptions import UserError


class EInvoiceLine(models.Model):
    _name = 'e.invoice.line'
    _description = 'E-Invoice Line'

    move_id = fields.Many2one('account.move', string='Invoice', ondelete='cascade')
    invoice_issuer = fields.Char(string='Invoice Issuer', required=True, compute='_compute_partner_info', store=True, readonly=False)
    tax_code = fields.Char(string='Tax Code', required=True, compute='_compute_partner_info', store=True, readonly=False)
    form_no = fields.Char(string='Form No.', required=True)
    serial = fields.Char(string='Serial', required=True)
    number = fields.Char(string='No', required=True)
    invoice_date = fields.Date(string='Invoice Date', required=True)

    currency_id = fields.Many2one(
        related='move_id.currency_id',
        string='Currency',
        store=True, readonly=True,
    )
    company_id = fields.Many2one('res.company', related='move_id.company_id', string='Company', store=True, readonly=True)

    goods_name = fields.Char(string='Goods/Service Name', required=True)
    product_uom = fields.Char(string='Unit of Measure', required=True)
    product_uom_qty = fields.Float(string='Quantity', default=1.0, digits='Product Unit of Measure', required=True)
    price_unit = fields.Float(string='Unit Price', required=True)

    # === Price & Tax fields === #
    price_subtotal = fields.Monetary(
        string='Untaxed Subtotal',
        currency_field='currency_id'
    )
    price_total = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id'
    )
    taxes_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})
    price_tax = fields.Float(string='Tax Amount')

    @api.depends('move_id.partner_id')
    def _compute_partner_info(self):
        for line in self:
            partner = line.move_id.partner_id
            line.invoice_issuer = line.invoice_issuer or partner.name
            line.tax_code = line.tax_code or partner.vat
