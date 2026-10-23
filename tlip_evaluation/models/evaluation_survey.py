from odoo import api, models, fields


class EvaluationSurvey(models.Model):
    _name = "evaluation.survey"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Evaluation Survey"

    evaluation_date = fields.Date(default=lambda: fields.Date.today(), tracking=True)
    reviewer_id = fields.Many2one(
        "hr.employee",
        string="Reviewer",
        default=lambda self: self.env.user.employee_id.id,
        tracking=True,
    )
    position_id = fields.Many2one(
        "hr.job", string="Position", related="reviewer_id.job_id"
    )
    department_id = fields.Many2one(
        "hr.department", string="Department", related="reviewer_id.department_id"
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("cancel", "Cancel"),
        ],
        string="State",
        default="draft",
        required=True,
        tracking=True,
    )
    evaluation_type = fields.Selection(
        selection=[
            ("rfq_vendor_selection", "RFQ & Vendor Selection"),
            ("post_transaction", "Post-transaction"),
            ("periodical", "Periodical"),
        ],
        string="Type of Evaluation",
        required=True,
        tracking=True,
    )
    survey_criteria_ids = fields.One2many("evaluation.survey.criteria", "survey_id")
    survey_score = fields.Float(
        string="Survey Score",
        compute="_compute_survey_score",
        store=True,
    )

    @api.depends("survey_criteria_ids.score")
    def _compute_survey_score(self):
        for survey in self:
            survey.survey_score = sum(
                criteria.score for criteria in survey.survey_criteria_ids
            )

    @api.depends("partner_id", "evaluation_date")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for rec in self:
            rec.display_name = f"{rec.partner_id.name} ({rec.evaluation_date})"
        return res

    def button_submit(self):
        self.state = "confirm"

    def button_cancel(self):
        self.state = "cancel"

    def button_reset(self):
        self.state = "draft"

    @api.model_create_multi
    def create(self, vals_list):
        EvaluationCriteria = self.env["evaluation.criteria"]
        EvaluationQuestion = self.env["evaluation.question"]

        for vals in vals_list:
            evaluation_type = vals.get("evaluation_type")

            if evaluation_type:
                survey_criteria_vals = self._prepare_survey_criteria_question_vals(
                    EvaluationCriteria, EvaluationQuestion, evaluation_type
                )
                vals["survey_criteria_ids"] = survey_criteria_vals

        return super(EvaluationSurvey, self).create(vals_list)

    @api.model
    def _prepare_survey_criteria_question_vals(
        self, evaluation_criteria, evaluation_question, evaluation_type
    ):
        survey_criteria_vals = [(5, 0, 0)]
        criterias = evaluation_criteria.search(
            [("evaluation_type", "=", evaluation_type)]
        )

        for criteria in criterias:
            survey_question_vals = [(5, 0, 0)]
            question_records = evaluation_question.search(
                [("evaluation_criteria_id", "=", criteria.id)]
            )

            for question in question_records:
                survey_question_vals.append(
                    (0, 0, {"evaluation_question_id": question.id})
                )

            survey_criteria_vals.append(
                (0, 0, {
                    "evaluation_criteria_id": criteria.id,
                    "survey_question_ids": survey_question_vals
                })
            )

        return survey_criteria_vals
