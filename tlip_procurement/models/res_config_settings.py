from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    employee_purchase_quota = fields.Float(
        string="Purchase Quota",
        help="The maximum amount that can be requested",
        related="company_id.employee_purchase_quota",
        readonly=False,
    )
    minimum_biding_amount = fields.Monetary(
        string="Minimum Biding Amount",
        readonly=False,
        related="company_id.minimum_biding_amount",
    )
    minimum_preference_check_amount = fields.Monetary(
        string="Minimum Preference Check Amount",
        readonly=False,
        related="company_id.minimum_preference_check_amount",
    )
    purchase_contract_bypass_maximum = fields.Monetary(
        string="Maximum Amount By Pass Purchase Contract",
        readonly=False,
        related="company_id.purchase_contract_bypass_maximum",
    )
