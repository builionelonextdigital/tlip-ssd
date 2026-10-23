from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    employee_purchase_quota = fields.Float(
        string="Purchase Quota",
        help="The maximum amount that can be requested",
    )
    minimum_biding_amount = fields.Monetary(
        string="Minimum Biding Amount"
    )
    minimum_preference_check_amount = fields.Monetary(
        string="Minimum Preference Check Amount"
    )
    purchase_contract_bypass_maximum = fields.Monetary(
        string="Maximum Amount By Pass Purchase Contract"
    )

    @api.constrains("minimum_biding_amount")
    def check_minimum_biding_amount(self):
        for record in self:
            if record.minimum_biding_amount < 0:
                raise ValidationError(_("The minimum bidding amount should be positive"))

    @api.constrains("minimum_preference_check_amount")
    def check_minimum_preference_check_amount(self):
        for record in self:
            if record.minimum_preference_check_amount < 0:
                raise ValidationError(_("The minimum preference check amount should be positive"))
