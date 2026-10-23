from odoo import fields, models


class BudgetCodeDetail(models.Model):
    _name = "budget.line.detail"
    _description = "Budget Code Detail"

    budget_line_id = fields.Many2one(
        comodel_name="budget.line",
        ondelete="cascade"
    )
    product_categ_id = fields.Many2one(
        'product.category', string='Item Category',
        required=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='budget_line_id.currency_id'
    )
    budget_amount = fields.Monetary(
        string='Budget',
    )
    committed_amount = fields.Monetary(
        string='Reserved',
    )
    achieved_amount = fields.Monetary(
        string='Used',
    )
