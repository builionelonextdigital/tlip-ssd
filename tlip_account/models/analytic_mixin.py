from odoo import models, _
from odoo.exceptions import UserError


class AnalyticMixin(models.AbstractModel):
    _inherit = "analytic.mixin"

    def get_department_job_on_analytic_distribution(self, record_name=None, company_id=None):
        """
        Retrieve the department job based on the analytic distribution.
        Note: This method should be used with `ensure_one` if `analytic_distribution` exists in the main record; otherwise, it should be applied to multiple lines within the same parent record.
        :return: The department job.
        """
        if not company_id:
            company_id = self.env.company.id

        budget_code_ids = set(
            int(key)
            for distribution in self.mapped("analytic_distribution")
            if distribution
            for key in dict(distribution).keys()
        )

        budget_departments = self.env["account.analytic.account"]\
            .browse(budget_code_ids).budget_department_id.with_context(company_id=company_id)

        # One budget department, return its job_id
        if len(budget_departments) <= 1:
            return budget_departments.job_id

        # Case multiple budget departments, get their budget department group
        budget_department_groups = budget_departments.department_group_id
        if len(budget_department_groups) > 1:
            # Ensure that procurement task line will have one budget department group
            error_message = _("Do not allow multiple budget department group.")
            if record_name:
                error_message = f"[{record_name}]" + " - " + error_message

            raise UserError(error_message)

        budget_department_groups = budget_departments.department_group_id.with_context(
            company_id=company_id
        )
        return budget_department_groups.job_id
