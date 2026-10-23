from odoo import models, fields


class EvaluationSurveyInherit(models.Model):
    _inherit = "evaluation.survey"

    po_id = fields.Many2one(
        "purchase.order", 
        string="Purchase Order"
    )
