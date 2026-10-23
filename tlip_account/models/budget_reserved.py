from odoo import fields, models


class BudgetReserved(models.Model):
    _name = "budget.reserved"
    _description = "Budget Reserved"

    account_id = fields.Many2one(
        comodel_name="account.analytic.account", string="Budget Account", required=True
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    name = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount")
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
