from odoo import api, models, fields, _
from odoo.exceptions import UserError


RATINGMAPPING = {"poor": 0, "average": 1, "excellent": 2}


class SurveyQuestion(models.Model):
    _name = "evaluation.survey.question"
    _description = " Survey Question"

    survey_criteria_id = fields.Many2one("evaluation.survey.criteria")
    evaluation_question_id = fields.Many2one("evaluation.question")
    question = fields.Char(string="Question", compute="_compute_question", store=True)
    rating = fields.Selection(
        selection=[
            ("poor", "Poor"),
            ("average", "Average"),
            ("excellent", "Excellent"),
        ],
        string="Rating",
    )

    @api.depends("evaluation_question_id")
    def _compute_question(self):
        for rec in self:
            rec.question = (
                rec.evaluation_question_id.question
                if rec.evaluation_question_id
                else rec.question
            )

    def action_calculate_questions_score(self):
        return sum(RATINGMAPPING.get(question.rating, 0) for question in self)

    def unlink(self):
        for rec in self:
            if rec.evaluation_question_id:
                # Since user can add question to survey criteria, user can remove lines they create but not the default lines (having evaluation_question_id)
                raise UserError(
                    _(f"Do not allow to remove question {rec.question}.")
                )
        return super().unlink()
