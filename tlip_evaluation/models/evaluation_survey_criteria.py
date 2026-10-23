from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SurveyCriteria(models.Model):
    _name = "evaluation.survey.criteria"
    _description = "Survey Criteria"

    evaluation_criteria_id = fields.Many2one(
        "evaluation.criteria", string="Criteria for Evaluation"
    )
    survey_id = fields.Many2one("evaluation.survey")
    state = fields.Selection(related="survey_id.state")
    evaluation_type = fields.Selection(
        related="evaluation_criteria_id.evaluation_type", string="Evaluation Type"
    )
    score = fields.Float(string="Score", compute="_compute_score", store=True)
    survey_question_ids = fields.One2many(
        "evaluation.survey.question", "survey_criteria_id", string="Questions"
    )
    existing_criteria_ids = fields.Many2many(
        "evaluation.criteria",
        string="Existing Criteria",
        compute="_compute_existing_criteria",
    )

    @api.depends("evaluation_criteria_id", "survey_question_ids.rating")
    def _compute_score(self):
        for rec in self:
            score = 0
            if rec.evaluation_criteria_id and rec.survey_question_ids:
                questions_score = rec.survey_question_ids.action_calculate_questions_score()
                criteria_score = rec.evaluation_criteria_id.action_calculate_criteria_score(
                    questions_score
                )
                score = criteria_score

            rec.score = score

    @api.depends("survey_id.survey_criteria_ids")
    def _compute_existing_criteria(self):
        for record in self:
            criteria_ids = record.survey_id.survey_criteria_ids.mapped(
                "evaluation_criteria_id"
            )
            record.existing_criteria_ids = [(6, 0, criteria_ids.ids)]

    def action_open_questions(self):
        return {
            "name": self.evaluation_criteria_id.name or "Survey Questions",
            "type": "ir.actions.act_window",
            "views": [[self.env.ref("tlip_evaluation.view_evaluation_survey_criteria_form").id, "form"]],
            "res_model": "evaluation.survey.criteria",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_update_questions(self):
        self.ensure_one()
        if not all(self.survey_question_ids.mapped("rating")):
            raise UserError(_("Please update rating to question."))

    def unlink(self):
        for rec in self:
            if rec.evaluation_type == rec.survey_id.evaluation_type:
                # User are not allowed to remove criteria that are default in the survey (having evaluation_type same as survey evaluation_type)
                raise UserError(
                    _(f"Do not allow to remove criteria line {rec.evaluation_criteria_id.name}.")
                )
        return super().unlink()
