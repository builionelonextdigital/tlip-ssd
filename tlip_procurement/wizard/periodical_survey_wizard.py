from odoo import models, fields


class PeriodicalSurveyWizard(models.TransientModel):
    _name = "periodical.survey.wizard"
    _description = "Create a Series of Periodical Supplier Evaluations"

    partner_ids = fields.Many2many(
        "res.partner",
        string="Supplier",
    )

    def action_create_evaluation_surveys(self):
        self.ensure_one()

        survey_vals = self._prepare_evaluation_survey_vals()
        evaluations = self.env["evaluation.survey"].create(survey_vals)

        context = dict(self.env.context) or {}
        action = self.env["ir.actions.actions"]._for_xml_id(
            "tlip_evaluation.evaluation_survey_action"
        )
        action.update(
            {
                "name": "Create a series of periodical supplier evaluations",
                "domain": [("id", "in", evaluations.ids)],
                "context": context,
                "target": "main",
            }
        )

        return action

    def _prepare_evaluation_survey_vals(self):
        return [
            {
                "partner_id": partner.id,
                "evaluation_date": fields.Date.today(),
                "evaluation_type": "periodical",
            }
            for partner in self.partner_ids
        ]
