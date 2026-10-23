from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    bank_exchange_rate_id = fields.Many2one(
        comodel_name="res.bank",
        string="Default Bank Exchange Rate",
        readonly=False,
        related="company_id.bank_exchange_rate_id",
    )
    deposit_percent_amount = fields.Float(
        string="Deposit Percent Amount",
        related="company_id.deposit_percent_amount",
        readonly=False,
    )