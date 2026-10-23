# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, osv
from collections import defaultdict


class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_accounts = fields.Boolean(
        string="Accounts",
        compute=lambda x: x._compute_report_option_filter('filter_accounts'), readonly=False, store=True, depends=['root_report_id', 'section_main_report_ids'],
    )
    
    ####################################################
    # OPTIONS: analytic filter
    ####################################################

    def _init_options_accounts(self, options, previous_options):
        if not self.filter_accounts:
            return
        previous_account_accounts = previous_options.get('account_accounts', [])
        account_account_ids = [int(x) for x in previous_account_accounts]
        selected_account_accounts = self.env['account.account'].search([('id', 'in', account_account_ids)])

        options['display_accounts'] = True
        options['account_accounts'] = selected_account_accounts.ids
        options['selected_account_account_names'] = selected_account_accounts.mapped('name')
        
    def get_report_information(self, options):
        res = super(AccountReport, self).get_report_information(options)
        if res.get('filters', {}):
            res['filters'].update({
                'show_accounts': options.get('display_accounts', False),
            })
        return res
    
    def _get_options_domain(self, options, date_scope):
        self.ensure_one()
        domain = super()._get_options_domain(options, date_scope)

        # Get the analytic accounts that we need to filter on from the options and add a domain for them.
        if 'account_accounts' in options and options.get('account_accounts', []):
            domain = osv.expression.AND([
                domain,
                [('account_id', 'in', options.get('account_accounts', []))],
            ])

        return domain
