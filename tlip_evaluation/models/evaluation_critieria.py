import logging
from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class EvaluationCriteria(models.Model):
    _name = "evaluation.criteria"
    _description = "Critera for Evaluation "

    DEFAULT_CODE_CONTENT = """# Available variables:
#  - question_score: Total score from questions for each criteria - Type number
#  - today: current date when the contract is running
# Return score for the criteria
# Note: returned value have to be set in the variable result.
# For example: result = question_score / 8 * 20\n\n
result = question_score
"""

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    formula = fields.Text(string="Formula", default=DEFAULT_CODE_CONTENT, required=True)
    evaluation_type = fields.Selection(
        selection=[
            ("rfq_vendor_selection", "RFQ & Vendor Selection"),
            ("post_transaction", "Post-Transaction"),
            ("periodical", "Periodical"),
        ],
        string="Type of Evaluation",
        required=True,
    )

    @api.depends('name', 'evaluation_type')
    def _compute_display_name(self):
        for record in self:
            eval_type = dict(record._fields['evaluation_type'].selection).get(record.evaluation_type, '')
            record.display_name = f"[{eval_type}] {record.name}"

    def action_calculate_criteria_score(self, question_score=0):
        self.ensure_one()
        localdict = {"today": fields.Date.today(), "question_score": question_score}
        return self._calculate_criteria_score(localdict)

    def _calculate_criteria_score(self, localdict):
        try:
            safe_eval(self.formula, localdict, mode="exec", nocopy=True)
        except Exception as e:
            _logger.error(e)
            return 0

        result = localdict.get("result", 0)
        return result
