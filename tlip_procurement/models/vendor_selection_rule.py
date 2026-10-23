from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class VendorSelectionRule(models.Model):
    _name = "vendor.selection.rule"
    _description = "Vendor Selection Rule"

    minimum_amount = fields.Monetary(string="Min Value (VND)", help="Indicate minimum amount for procurement task total amount range. If minimum is set and maximum is 0, then maximum refers to Inifinity")
    maximum_amount = fields.Monetary(string="Max Value (VND)", help="Indicate maximum amount for procurement task total amount range. If minimum is set and maximum is 0, then maximum refers to Inifinity")
    minimum_selected_vendors = fields.Integer(string="Min Selected Vendors")
    currency_id = fields.Many2one('res.currency', string='Loại tiền',
                                  default=lambda self: self.env.company.currency_id)
    is_maximum_infinity = fields.Boolean(compute="_compute_is_maximum_infinity")

    @api.constrains("minimum_amount", "maximum_amount")
    def check_minimum_amount(self):
        for record in self:
            if record.minimum_amount < 0:
                raise ValidationError(_("The minimum amount should be positive"))

            if record.maximum_amount < 0:
                raise ValidationError(_("The maximum amount should be positive"))
            
            if record.minimum_amount > record.maximum_amount and not record.is_maximum_infinity:
                raise ValidationError(_("The minimum amount should be not be larger than maximum amount"))

    @api.constrains("minimum_selected_vendors")
    def check_minimum_selected_vendors(self):
        for record in self:
            if record.minimum_selected_vendors < 0:
                raise ValidationError(_("The minimum selected vendors should be positive"))
            
    @api.depends("minimum_amount", "maximum_amount")
    def _compute_is_maximum_infinity(self):
        for record in self:
            # Example: min = 1000, max = 0 
            # Range: 1000 -> inf
            record.is_maximum_infinity = record.minimum_amount > 0 and record.maximum_amount == 0
