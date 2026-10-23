import ast
from odoo import models


class AccountReportInherit(models.Model):
    _inherit = "account.report"

    def execute_action(self, options, params=None):
        action_read = super().execute_action(options, params=params)
        # customize action for CIP WIP Summary report journal items view
        if action_read.get('xml_id', '') == 'tlip_account.action_cip_wip_summary_view_detail':
            development_project_id = params.get('id').split('_')[1]
            date_from = options['date']['date_from']
            date_to = options['date']['date_to']
            #TODO: add domain by analytic account
            # if analytic_account_id:
            # domain.append(('analytic_distribution', '!=', False))
            ml_ids = params.get('id').split('_')[-1].replace('~~','') if len(params.get('id').split('_')) > 4 else []
            domain = [
                ('parent_state', '=', 'posted'),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('development_project_id', '=', int(development_project_id)),
                ('id', 'in', ast.literal_eval(ml_ids))
            ]
            action_read['domain'] = domain
        return action_read