from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    evaluation_survey_ids = fields.One2many(
        "evaluation.survey", "partner_id", string="Evaluation Surveys"
    )
    last_evaluation_date = fields.Date(
        string="Last Evaluation Date",
        compute="_compute_evaluation_survey_data",
    )
    total_score = fields.Float(
        string="Total Score",
        compute="_compute_evaluation_survey_data",
    )

    @api.depends("evaluation_survey_ids.state", "evaluation_survey_ids")
    def _compute_evaluation_survey_data(self):
        for partner in self:
            confirmed_surveys = partner.evaluation_survey_ids.filtered(
                lambda s: s.state == "confirm"
            )
            if confirmed_surveys:
                sorted_surveys = confirmed_surveys.sorted(
                    key=lambda s: s.write_date, reverse=True
                )
                partner.last_evaluation_date = sorted_surveys[0].evaluation_date
                partner.total_score = sum(
                    [
                        self._calculate_survey_score_by_type(
                            sorted_surveys,
                            [("evaluation_type", "=", "rfq_vendor_selection")],
                        ),
                        self._calculate_survey_score_by_type(
                            sorted_surveys,
                            [("evaluation_type", "=", "post_transaction")],
                        ),
                        self._calculate_survey_score_by_type(
                            sorted_surveys,
                            [("evaluation_type", "=", "periodical")],
                        ),
                    ]
                )
            else:
                partner.last_evaluation_date = False
                partner.total_score = 0.0

    @api.model
    def _calculate_survey_score_by_type(self, surveys, domain):
        filtered_surveys = surveys.filtered_domain(domain)
        return filtered_surveys[0].survey_score if filtered_surveys else 0
