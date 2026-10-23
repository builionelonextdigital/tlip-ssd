# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _custom_query_get(self, options, date_scope, domain=None, account_group_by=None):
        domain = self._get_options_domain(options, date_scope) + (domain or [])
        if account_group_by:
            domain = [do for do in domain if isinstance(do, str) or (isinstance(do, tuple) and do[0] != "analytic_distribution")]
        if options.get('forced_domain'):
            # That option key is set when splitting options between column groups
            domain += options['forced_domain']

        self.env['account.move.line'].check_access_rights('read')

        query = self.env['account.move.line']._where_calc(domain)

        # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
        self.env['account.move.line']._apply_ir_rules(query)

        return query.get_sql()