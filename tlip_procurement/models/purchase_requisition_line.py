from odoo import models, fields, api
from ..tools.misc import format_decimal


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    purchase_supplement_id = fields.Many2one('purchase.supplement', 'Purchase Supplement')
    tax_rate = fields.Float('VAT Rate')
    amount_tax = fields.Float('VAT Amount', compute='_compute_price')
    price_total = fields.Float('Amount Total', compute='_compute_price')
    specification = fields.Text(string='Specification')
    product_uom_id_vn = fields.Char(related='product_uom_id.uom_invoice_vn')
    price_unit_vn_text = fields.Char(compute='_compute_price')
    price_unit_en_text = fields.Char(compute='_compute_price')
    price_total_vn_text = fields.Char(compute='_compute_price')
    price_total_en_text = fields.Char(compute='_compute_price')
    line_number = fields.Integer('No.', compute='_compute_line_number')

    @api.depends('product_qty', 'price_unit', 'tax_rate')
    def _compute_price(self):
        odoo_env = self.env
        for line in self:
            line.amount_tax = (line.product_qty * line.price_unit * line.tax_rate) / 100
            price_total = (line.product_qty * line.price_unit) + line.amount_tax

            line.price_total = price_total
            line.price_unit_vn_text = format_decimal(odoo_env, line.price_unit, lang='vi_VN')
            line.price_unit_en_text = format_decimal(odoo_env, line.price_unit, lang='en_US')
            line.price_total_vn_text = format_decimal(odoo_env, line.price_total, lang='vi_VN')
            line.price_total_en_text = format_decimal(odoo_env, line.price_total, lang='en_US')

    @api.depends('requisition_id', 'requisition_id.line_ids')
    def _compute_line_number(self):
        for record in self:
            line_ids = record.requisition_id.line_ids
            record.line_number = line_ids._origin.ids.index(record._origin.id) + 1 if record._origin.id in line_ids._origin.ids else 1

    def calculate_budget_on_account(self, account_mapping, currency_rate, is_original):
        """Calculate reserved amounts based on requisition lines with analytic distribution."""
        for line in self.filtered(lambda l: l.analytic_distribution):
            for account, rate in line.analytic_distribution.items():
                line_amount = (
                    line.price_total * (rate / 100.0)
                ) / (currency_rate or 1.0)

                if is_original:
                    line_amount *= -1
                account_mapping[int(account)] += line_amount
