from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    mysign_config_ids = fields.One2many(
        comodel_name="mysign.config",
        inverse_name="company_id",
        string="MySign Configurations",
    )
    mysign_account_id = fields.Many2one(
        comodel_name="mysign.account",
        string="MySign Account",
    )
