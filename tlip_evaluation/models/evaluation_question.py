from odoo import models, fields


class EvaluationQuestion(models.Model):
    _name = "evaluation.question"
    _description = "Questions for Evaluation"

    evaluation_criteria_id = fields.Many2one(
        "evaluation.criteria", string="Criteria for Evaluation", required=True
    )
    evaluation_type = fields.Selection(
        related="evaluation_criteria_id.evaluation_type",
        string="Type of Evaluation"
    )
    question = fields.Char(string="Question", required=True)
