from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    latest_purchased_date = fields.Datetime(compute="_compute_latest_purchased_date")
    frequency = fields.Selection(selection=[
        ('infrequent', 'Infrequent'),
        ('over_12mo', '> 12 months'),
        ('recursive', 'Recursive')
    ], string="Procurement Frequency")
    number_of_months = fields.Integer(string='# Months')

    @tools.ormcache()
    def _get_default_category_id(self):
        return self.env.ref('tlip_procurement.product_category_rfq')
    
    @api.constrains("frequency", "number_of_months")
    def _constrains_number_of_months(self):
        for product in self:
            if product.frequency == "recursive" and product.number_of_months <= 0:
                raise UserError(_("Number of months should be larger than 0"))

    def _compute_latest_purchased_date(self):
        self.mapped("product_variant_ids").mapped("purchase_line_ids")
        for rec in self:
            related_purchase_orders = rec.product_variant_ids.purchase_line_ids.order_id
            orders = related_purchase_orders.filtered(lambda order: order.state in ('purchase', 'done') and \
                                                                    order.date_approve)
            rec.latest_purchased_date = orders and max(orders.mapped("date_approve")) or False

    @api.model
    def create(self, vals):
        if vals.get('categ_id', False) == self.env.ref('product.product_category_all').id:
            vals['categ_id'] = self.env.ref('tlip_procurement.product_category_rfq').id
        return super().create(vals)
class ProductProduct(models.Model):
    _inherit = 'product.product'

    purchase_line_ids = fields.One2many('purchase.order.line', 'product_id', string="Purchase Lines")
