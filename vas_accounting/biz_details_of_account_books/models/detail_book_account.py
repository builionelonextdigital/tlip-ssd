# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import io
import zipfile
import base64

from odoo import models, fields, api, _
from odoo.tools import SQL
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, xlsxwriter

from datetime import timedelta, datetime
from collections import defaultdict


class DetailBookAccount(models.AbstractModel):
    _name = 'detail.book.account'
    _inherit = 'account.report.custom.handler'
    _description = 'Detail of book account BTC (S38-DN)'

    def _custom_options_initializer(self, report, options, previous_options=None):
        # Remove multi-currency columns if needed
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        # Automatically unfold the report when printing it, unless some specific lines have been unfolded
        options['unfold_all'] = (self._context.get('print_mode') and not options.get('unfolded_lines')) or options['unfold_all']

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        lines = []
        date_from = fields.Date.from_string(options['date']['date_from'])
        company_currency = self.env.company.currency_id

        totals_by_column_group = defaultdict(lambda: {'debit': 0, 'credit': 0, 'balance': 0})
        for account, column_group_results in self._query_values(report, options):
            eval_dict = {}
            has_lines = False
            for column_group_key, results in column_group_results.items():
                account_sum = results.get('sum', {})
                account_un_earn = results.get('unaffected_earnings', {})

                account_debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
                account_credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
                account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

                eval_dict[column_group_key] = {
                    'debit': account_debit,
                    'credit': account_credit,
                    'balance': account_balance,
                }

                max_date = account_sum.get('max_date')
                has_lines = has_lines or (max_date and max_date >= date_from)

                totals_by_column_group[column_group_key]['debit'] += account_debit
                totals_by_column_group[column_group_key]['credit'] += account_credit
                totals_by_column_group[column_group_key]['balance'] += account_balance

            lines.append(self._get_account_title_line(report, options, account, has_lines, eval_dict))

        # Report total line.
        for totals in totals_by_column_group.values():
            totals['balance'] = company_currency.round(totals['balance'])

        # Tax Declaration lines.
        journal_options = report._get_options_journals(options)
        if len(options['column_groups']) == 1 and len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
            lines += self._tax_declaration_lines(report, options, journal_options[0]['type'])

        # Total line
        lines.append(self._get_total_line(report, options, totals_by_column_group))

        return [(0, line) for line in lines]

    def _custom_unfold_all_batch_data_generator(self, report, options, lines_to_expand_by_function):
        account_ids_to_expand = []
        for line_dict in lines_to_expand_by_function.get('_report_expand_unfoldable_line_general_ledger', []):
            model, model_id = report._get_model_info_from_id(line_dict['id'])
            if model == 'account.account':
                account_ids_to_expand.append(model_id)

        return {
            'initial_balances': self._get_initial_balance_values(report, account_ids_to_expand, options),

            # load_more_limit canno( be passed to this call, otherwise it won't be applied per account but on the whole result.
            # We gain perf from batching, but load every result, even if the limit restricts them later.
            'aml_values': self._get_aml_values(report, options, account_ids_to_expand),
        }

    def _tax_declaration_lines(self, report, options, tax_type):
        labels_replacement = {
            'debit': _("Base Amount"),
            'credit': _("Tax Amount"),
        }

        rslt = [{
            'id': report._get_generic_line_id(None, None, markup='tax_decl_header_1'),
            'name': _('Tax Declaration'),
            'columns': [{} for column in options['columns']],
            'level': 1,
            'unfoldable': False,
            'unfolded': False,
        }, {
            'id': report._get_generic_line_id(None, None, markup='tax_decl_header_1'),
            'name': _('Name'),
            'columns': [{'name': labels_replacement.get(col['expression_label'], '')} for col in options['columns']],
            'level': 2,
            'unfoldable': False,
            'unfolded': False,
        }]

        # Call the generic tax report
        generic_tax_report = self.env.ref('account.generic_tax_report')
        tax_report_options = generic_tax_report.get_options({**options, 'report_id': generic_tax_report.id, 'forced_domain': [('tax_line_id.type_tax_use', '=', tax_type)]})
        tax_report_lines = generic_tax_report._get_lines(tax_report_options)
        tax_type_parent_line_id = generic_tax_report._get_generic_line_id(None, None, markup=tax_type)

        for tax_report_line in tax_report_lines:
            if tax_report_line.get('parent_id') == tax_type_parent_line_id:
                original_columns = tax_report_line['columns']
                row_column_map = {
                    'debit': original_columns[0],
                    'credit': original_columns[1],
                }

                tax_report_line['columns'] = [row_column_map.get(col['expression_label'], {}) for col in options['columns']]
                rslt.append(tax_report_line)

        return rslt

    def _query_values(self, report, options):
        """ Executes the queries, and performs all the computations.

        :return:    [(record, values_by_column_group), ...],  where
                    - record is an account.account record.
                    - values_by_column_group is a dict in the form {column_group_key: values, ...}
                        - column_group_key is a string identifying a column group, as in options['column_groups']
                        - values is a list of dictionaries, one per period containing:
                            - sum:                              {'debit': float, 'credit': float, 'balance': float}
                            - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                            - (optional) unaffected_earnings:   {'debit': float, 'credit': float, 'balance': float}
        """
        # Execute the queries and dispatch the results.
        query = self._get_query_sums(report, options)

        if not query:
            return []

        groupby_accounts = {}
        groupby_companies = {}

        self._cr.execute(query)
        for res in self._cr.dictfetchall():
            # No result to aggregate.
            if res['groupby'] is None:
                continue

            column_group_key = res['column_group_key']
            key = res['key']
            if key == 'sum':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_accounts[res['groupby']][column_group_key][key] = res

            elif key == 'initial_balance':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_accounts[res['groupby']][column_group_key][key] = res

            elif key == 'unaffected_earnings':
                groupby_companies.setdefault(res['groupby'], {col_group_key: {} for col_group_key in options['column_groups']})
                groupby_companies[res['groupby']][column_group_key] = res

        # Affect the unaffected earnings to the first fetched account of type 'account.data_unaffected_earnings'.
        # There is an unaffected earnings for each company but it's less costly to fetch all candidate accounts in
        # a single search and then iterate it.
        if groupby_companies:
            unaffected_earnings_accounts = self.env['account.account'].search([
                ('display_name', 'ilike', options.get('filter_search_bar')),
                *self.env['account.account']._check_company_domain(list(groupby_companies.keys())),
                ('account_type', '=', 'equity_unaffected'),
            ])
            for company_id, groupby_company in groupby_companies.items():
                if equity_unaffected_account := unaffected_earnings_accounts.filtered(lambda a: self.env['res.company'].browse(company_id).root_id in a.company_ids):
                    for column_group_key in options['column_groups']:
                        groupby_accounts.setdefault(
                            equity_unaffected_account.id,
                            {col_group_key: {'unaffected_earnings': {}} for col_group_key in options['column_groups']},
                        )
                        if unaffected_earnings := groupby_company.get(column_group_key):
                            if groupby_accounts[equity_unaffected_account.id][column_group_key].get('unaffected_earnings'):
                                for key in ['amount_currency', 'debit', 'credit', 'balance']:
                                    groupby_accounts[equity_unaffected_account.id][column_group_key]['unaffected_earnings'][key] += unaffected_earnings[key]
                            else:
                                groupby_accounts[equity_unaffected_account.id][column_group_key]['unaffected_earnings'] = unaffected_earnings

        # Retrieve the accounts to browse.
        # groupby_accounts.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # - the unaffected earnings allocation.
        # Note a search is done instead of a browse to preserve the table ordering.
        if groupby_accounts:
            accounts = self.env['account.account'].search([('id', 'in', list(groupby_accounts.keys()))])
        else:
            accounts = []

        return [(account, groupby_accounts[account.id]) for account in accounts]

    def _get_query_sums(self, report, options):
        """ Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :return:                    (query, params)
        """
        options_by_column_group = report._split_options_per_column_group(options)
        
        queries = []

        # Create the currency table.
        # As the currency table is the same whatever the comparisons, create it only once.
        ct_query = report._get_currency_table(options)

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================
        for column_group_key, options_group in options_by_column_group.items():
            if not options.get('general_ledger_strict_range'):
                options_group = self._get_options_sum_balance(options_group)

            # Sum is computed including the initial balance of the accounts configured to do so, unless a special option key is used
            # (this is required for trial balance, which is based on general ledger)
            sum_date_scope = 'strict_range' if options_group.get('general_ledger_strict_range') else 'from_beginning'

            query_domain = []

            if options.get('filter_search_bar'):
                query_domain.append(('account_id', 'ilike', options['filter_search_bar']))

            if options_group.get('include_current_year_in_unaff_earnings'):
                query_domain += [('account_id.include_initial_balance', '=', True)]

            query = report._get_report_query(options_group, sum_date_scope, domain=query_domain)
            queries.append(SQL(
                """
                    SELECT
                        account_move_line.account_id                                 AS groupby,
                        'sum'                                                        AS key,
                        MAX(account_move_line.date)                                  AS max_date,
                        %(column_group_key)s                                         AS column_group_key,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)        AS amount_currency,
                        SUM(account_move_line.debit * account_currency_table.rate)   AS debit,
                        SUM(account_move_line.credit * account_currency_table.rate)  AS credit,
                        SUM(account_move_line.balance * account_currency_table.rate) AS balance
                    FROM %(table_references)s
                    LEFT JOIN %(currency_table)s ON account_currency_table.company_id = account_move_line.company_id
                    WHERE %(search_condition)s
                    GROUP BY account_move_line.account_id
                """,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table=report._get_currency_table(options),
                search_condition=query.where_clause
            ))
        
            # ============================================
            # 2) Get sums for the unaffected earnings.
            # ============================================
            if not options_group.get('general_ledger_strict_range'):
                unaff_earnings_domain = [('account_id.include_initial_balance', '=', False)]

                # The period domain is expressed as:
                # [
                #   ('date' <= fiscalyear['date_from'] - 1),
                #   ('account_id.include_initial_balance', '=', False),
                # ]

                new_options = self._get_options_unaffected_earnings(options_group)
                query = report._get_report_query(new_options, 'strict_range', domain=unaff_earnings_domain)
                queries.append(SQL(
                    """
                        SELECT
                            account_move_line.company_id                            AS groupby,
                            'unaffected_earnings'                                   AS key,
                            NULL                                                    AS max_date,
                            %(column_group_key)s                                    AS column_group_key,
                            COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                            SUM(account_move_line.debit * account_currency_table.rate)   AS debit,
                            SUM(account_move_line.credit * account_currency_table.rate)  AS credit,
                            SUM(account_move_line.balance * account_currency_table.rate) AS balance
                        FROM %(table_references)s
                        LEFT JOIN %(currency_table)s ON account_currency_table.company_id = account_move_line.company_id
                        WHERE %(search_condition)s
                        GROUP BY account_move_line.company_id
                    """,
                    column_group_key=column_group_key,
                    table_references=query.from_clause,
                    currency_table=report._get_currency_table(new_options),
                    search_condition=query.where_clause,
                ))
                
        return SQL(" UNION ALL ").join(queries)

    def _get_options_unaffected_earnings(self, options):
        ''' Create options used to compute the unaffected earnings.
        The unaffected earnings are the amount of benefits/loss that have not been allocated to
        another account in the previous fiscal years.
        The resulting dates domain will be:
        [
          ('date' <= fiscalyear['date_from'] - 1),
          ('account_id.include_initial_balance', '=', False),
        ]
        :param options: The report options.
        :return:        A copy of the options.
        '''
        new_options = options.copy()
        new_options.pop('filter_search_bar', None)
        fiscalyear_dates = self.env.company.compute_fiscalyear_dates(fields.Date.from_string(options['date']['date_from']))

        # Trial balance uses the options key, general ledger does not
        new_date_to = fields.Date.from_string(new_options['date']['date_to']) if options.get('include_current_year_in_unaff_earnings') else fiscalyear_dates['date_from'] - timedelta(days=1)

        new_options['date'] = {
            'mode': 'single',
            'date_to': fields.Date.to_string(new_date_to),
        }

        return new_options

    def _get_aml_values(self, report, options, expanded_account_ids, offset=0, limit=None):
        rslt = {account_id: {} for account_id in expanded_account_ids}
        aml_query = self._get_query_amls(report, options, expanded_account_ids, offset=offset, limit=limit)
        self._cr.execute(aml_query)
        for aml_result in self._cr.dictfetchall():
            if aml_result['ref']:
                aml_result['communication'] = f"{aml_result['ref']} - {aml_result['name']}"
            else:
                aml_result['communication'] = aml_result['name']

            aml_id = self.env['account.move.line'].browse(int(aml_result['id']))
            ctp_account_name = ''
            if aml_id and aml_id.ctp_account_ids:
                ctp_account_name = ", ".join(aml_id.ctp_account_ids.mapped('code'))

            aml_result.update({
                'number': aml_id.move_id.name,
                'date_numbered': aml_id.date.strftime('%d/%m/%Y'),
                'explain': aml_id.name,
                'countered_accounts': ctp_account_name,
            })

            # The same aml can return multiple results when using account_report_cash_basis module, if the receivable/payable
            # is reconciled with multiple payments. In this case, the date shown for the move lines actually corresponds to the
            # reconciliation date. In order to keep distinct lines in this case, we include date in the grouping key.
            aml_key = (aml_result['id'], aml_result['date'])

            account_result = rslt[aml_result['account_id']]
            if not aml_key in account_result:
                account_result[aml_key] = {col_group_key: {} for col_group_key in options['column_groups']}

            already_present_result = account_result[aml_key][aml_result['column_group_key']]
            if already_present_result:
                # In case the same move line gives multiple results at the same date, add them.
                # This does not happen in standard GL report, but could because of custom shadowing of account.move.line,
                # such as the one done in account_report_cash_basis (if the payable/receivable line is reconciled twice at the same date).
                already_present_result['debit'] += aml_result['debit']
                already_present_result['credit'] += aml_result['credit']
                already_present_result['balance'] += aml_result['balance']
            else:
                account_result[aml_key][aml_result['column_group_key']] = aml_result

        return rslt

    def _get_query_amls(self, report, options, expanded_account_ids, offset=0, limit=None):
        """ Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:               The report options.
        :param expanded_account_ids:  The account.account ids corresponding to consider. If None, match every account.
        :param offset:                The offset of the query (used by the load more).
        :param limit:                 The limit of the query (used by the load more).
        :return:                      (query, params)
        """
        additional_domain = [('account_id', 'in', expanded_account_ids)] if expanded_account_ids is not None else None
        queries = []
        journal_name = self.env['account.journal']._field_to_sql('journal', 'name')
        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            # Get sums for the account move lines.
            # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
            query = report._get_report_query(group_options, domain=additional_domain, date_scope='strict_range')
            account_alias = query.join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
            account_type = self.env['account.account']._field_to_sql(account_alias, 'account_type')
            query = SQL(
                '''
                SELECT
                    account_move_line.id,
                    account_move_line.date,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    ROUND(account_move_line.debit * account_currency_table.rate, 2)   AS debit,
                    ROUND(account_move_line.credit * account_currency_table.rate, 2)  AS credit,
                    account_move_line.balance * account_currency_table.rate AS balance,
                    move.name                               AS move_name,
                    company.currency_id                     AS company_currency_id,
                    partner.name                            AS partner_name,
                    move.move_type                          AS move_type,
                    %(account_code)s                        AS account_code,
                    %(account_name)s                        AS account_name,
                    journal.code                            AS journal_code,
                    %(journal_name)s                        AS journal_name,
                    full_rec.id                             AS full_rec_name,
                    %(column_group_key)s                    AS column_group_key
                FROM %(table_references)s
                JOIN account_move move                      ON move.id = account_move_line.move_id
                LEFT JOIN %(currency_table)s ON account_currency_table.company_id = account_move_line.company_id
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
                WHERE %(search_condition)s
                ORDER BY account_move_line.date, account_move_line.move_name, account_move_line.id
                ''',
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table=report._get_currency_table(group_options),
                search_condition=query.where_clause,
            )

            queries.append(query)

        full_query = SQL(" UNION ALL ").join(SQL("(%s)", query) for query in queries)
        if offset:
            full_query = SQL('%s OFFSET %s ', full_query, offset)
        if limit:
            full_query = SQL('%s LIMIT %s ', full_query, limit)

        return full_query

    def _get_initial_balance_values(self, report, account_ids, options):
        """
        Get sums for the initial balance.
        """
        queries = []
        params = []
        for column_group_key, options_group in report._split_options_per_column_group(options).items():
            new_options = self._get_options_initial_balance(options_group)
            ct_query = report._get_currency_table(new_options)
            domain = [('account_id', 'in', account_ids)]
            if new_options.get('include_current_year_in_unaff_earnings'):
                domain += [('account_id.include_initial_balance', '=', True)]

            query = report._get_report_query(new_options, 'from_beginning', domain=domain)
            queries.append(SQL(
                """
                SELECT
                    account_move_line.account_id                                                          AS groupby,
                    'initial_balance'                                                                     AS key,
                    NULL                                                                                  AS max_date,
                    %(column_group_key)s                                                                  AS column_group_key,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)                                 AS amount_currency,
                    SUM(account_move_line.debit * account_currency_table.rate)   AS debit,
                    SUM(account_move_line.credit * account_currency_table.rate)  AS credit,
                    SUM(account_move_line.balance * account_currency_table.rate) AS balance
                FROM %(table_references)s
                LEFT JOIN %(currency_table)s ON account_currency_table.company_id = account_move_line.company_id
                WHERE %(search_condition)s
                GROUP BY account_move_line.account_id
                """,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table=report._get_currency_table(new_options),
                search_condition=query.where_clause,
            ))
            
        self._cr.execute(SQL(" UNION ALL ").join(queries))

        init_balance_by_col_group = {
            account_id: {column_group_key: {} for column_group_key in options['column_groups']}
            for account_id in account_ids
        }
        for result in self._cr.dictfetchall():
            init_balance_by_col_group[result['groupby']][result['column_group_key']] = result

        accounts = self.env['account.account'].browse(account_ids)
        return {
            account.id: (account, init_balance_by_col_group[account.id])
            for account in accounts
        }

    def _get_options_initial_balance(self, options):
        """ Create options used to compute the initial balances.
        The initial balances depict the current balance of the accounts at the beginning of
        the selected period in the report.
        The resulting dates domain will be:
        [
            ('date' <= options['date_from'] - 1),
            '|',
            ('date' >= fiscalyear['date_from']),
            ('account_id.include_initial_balance', '=', True)
        ]
        :param options: The report options.
        :return:        A copy of the options.
        """
        new_options = options.copy()
        date_to = new_options['comparison']['periods'][-1]['date_from'] if new_options.get('comparison', {}).get('periods') else new_options['date']['date_from']
        new_date_to = fields.Date.from_string(date_to) - timedelta(days=1)

        # Date from computation
        # We have two case:
        # 1) We are choosing a date that starts at the beginning of a fiscal year and we want the initial period to be
        # the previous fiscal year
        # 2) We are choosing a date that starts in the middle of a fiscal year and in that case we want the initial period
        # to be the beginning of the fiscal year
        date_from = fields.Date.from_string(new_options['date']['date_from'])
        current_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date_from)

        if date_from == current_fiscalyear_dates['date_from']:
            # We want the previous fiscal year
            previous_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date_from - timedelta(days=1))
            new_date_from = previous_fiscalyear_dates['date_from']
            include_current_year_in_unaff_earnings = True
        else:
            # We want the current fiscal year
            new_date_from = current_fiscalyear_dates['date_from']
            include_current_year_in_unaff_earnings = False

        new_options['date'] = {
            'mode': 'range',
            'date_from': fields.Date.to_string(new_date_from),
            'date_to': fields.Date.to_string(new_date_to),
        }
        new_options['include_current_year_in_unaff_earnings'] = include_current_year_in_unaff_earnings

        return new_options

    def _get_options_sum_balance(self, options):
        new_options = options.copy()

        if not options.get('general_ledger_strict_range'):
            # Date from
            date_from = fields.Date.from_string(new_options['date']['date_from'])
            current_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date_from)
            new_date_from = current_fiscalyear_dates['date_from']

            new_date_to = new_options['date']['date_to']

            new_options['date'] = {
                'mode': 'range',
                'date_from': fields.Date.to_string(new_date_from),
                'date_to': new_date_to,
            }

        return new_options

    ####################################################
    # COLUMN/LINE HELPERS
    ####################################################
    def _get_account_title_line(self, report, options, account, has_lines, eval_dict):
        line_columns = []
        for column in options['columns']:
            col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
            col_expr_label = column['expression_label']

            if col_value is None or (col_expr_label == 'amount_currency' and not account.currency_id):
                line_columns.append({})

            else:
                if col_expr_label == 'amount_currency':
                    formatted_value = report.format_value(options, col_value, currency=account.currency_id, figure_type=column['figure_type'])
                else:
                    formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'])

                line_columns.append({
                    'name': formatted_value,
                    'no_format': col_value,
                    'class': 'number',
                })

        unfold_all = self._context.get('print_mode') or options.get('unfold_all')
        line_id = report._get_generic_line_id('account.account', account.id)
        return {
            'id': line_id,
            'name': f'{account.code} {account.name}',
            'search_key': account.code,
            'columns': line_columns,
            'level': 1,
            'unfoldable': has_lines,
            'unfolded': has_lines and (line_id in options.get('unfolded_lines') or unfold_all),
            'expand_function': '_report_expand_unfoldable_line_general_ledger',
            'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
        }

    def _get_aml_line(self, report, parent_line_id, options, eval_dict, init_bal_by_col_group):
        line_columns = []
        for column in options['columns']:
            col_expr_label = column['expression_label']
            col_value = eval_dict[column['column_group_key']].get(col_expr_label)

            if col_value is None:
                line_columns.append({})
            else:
                col_class = 'number'

                if col_expr_label == 'amount_currency':
                    currency = self.env['res.currency'].browse(eval_dict[column['column_group_key']]['currency_id'])

                    if currency != self.env.company.currency_id:
                        formatted_value = report.format_value(options, col_value, currency=currency, figure_type=column['figure_type'])
                    else:
                        formatted_value = ''
                elif col_expr_label == 'date':
                    formatted_value = format_date(self.env, col_value)
                    col_class = 'date'
                elif col_expr_label == 'balance':
                    col_value += init_bal_by_col_group[column['column_group_key']]
                    formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'])
                elif col_expr_label == 'communication' or col_expr_label == 'partner_name':
                    col_class = 'o_account_report_line_ellipsis'
                    formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'])
                else:
                    formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'])
                    if col_expr_label not in ('debit', 'credit'):
                        col_class = ''

                line_columns.append({
                    'name': formatted_value,
                    'no_format': col_value,
                    'class': col_class,
                })

        aml_id = None
        move_name = None
        caret_type = None
        for column_group_dict in eval_dict.values():
            aml_id = column_group_dict.get('id', '')
            if aml_id:
                if column_group_dict.get('payment_id'):
                    caret_type = 'account.payment'
                else:
                    caret_type = 'account.move.line'
                move_name = column_group_dict['move_name']
                break

        return {
            'id': report._get_generic_line_id('account.move.line', aml_id, parent_line_id=parent_line_id),
            'caret_options': caret_type,
            'parent_id': parent_line_id,
            'name': move_name,
            'columns': line_columns,
            'level': 2,
        }

    @api.model
    def _get_total_line(self, report, options, eval_dict):
        line_columns = []
        for column in options['columns']:
            col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
            if col_value is None:
                line_columns.append({})
            else:
                formatted_value = report.format_value(options, col_value, figure_type='monetary')
                line_columns.append({
                    'name': formatted_value,
                    'no_format': col_value,
                    'class': 'number',
                })

        return {
            'id': report._get_generic_line_id(None, None, markup='total'),
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': line_columns,
        }

    def caret_option_audit_tax(self, options, params):
        return self.env['account.generic.tax.report.handler'].caret_option_audit_tax(options, params)

    def _report_expand_unfoldable_line_general_ledger(self, line_dict_id, groupby, options, progress, offset, unfold_all_batch_data=None):
        def init_load_more_progress(line_dict):
            return {
                column['column_group_key']: line_col.get('no_format', 0)
                for column, line_col in  zip(options['columns'], line_dict['columns'])
                if column['expression_label'] == 'balance'
            }

        report = self.env.ref('account_reports.general_ledger_report')
        model, model_id = report._get_model_info_from_id(line_dict_id)

        if model != 'account.account':
            raise UserError(_("Wrong ID for general ledger line to expand: %s", line_dict_id))

        lines = []

        # Get initial balance
        if offset == 0:
            if unfold_all_batch_data:
                account, init_balance_by_col_group = unfold_all_batch_data['initial_balances'][model_id]
            else:
                account, init_balance_by_col_group = self._get_initial_balance_values(report, [model_id], options)[model_id]

            initial_balance_line = self._get_partner_and_general_ledger_initial_balance_line(report, options, line_dict_id, init_balance_by_col_group, account.currency_id)

            if initial_balance_line:
                lines.append(initial_balance_line)

                # For the first expansion of the line, the initial balance line gives the progress
                progress = init_load_more_progress(initial_balance_line)

        # Get move lines
        limit_to_load = report.load_more_limit + 1 if report.load_more_limit and not self._context.get('print_mode') else None

        if unfold_all_batch_data:
            aml_results = unfold_all_batch_data['aml_values'][model_id]
        else:
            aml_results = self._get_aml_values(report, options, [model_id], offset=offset, limit=limit_to_load)[model_id]

        has_more = False
        treated_results_count = 0
        next_progress = progress
        for aml_result in aml_results.values():
            if limit_to_load and treated_results_count == report.load_more_limit:
                # Enough elements loaded. Only the one due to the +1 in the limit passed when computing aml_results is left.
                # This element won't generate a line now, but we use it to know that we'll need to add a load_more line.
                has_more = True
                break

            new_line = self._get_aml_line(report, line_dict_id, options, aml_result, next_progress)
            lines.append(new_line)
            next_progress = init_load_more_progress(new_line)
            treated_results_count += 1

        return {
            'lines': lines,
            'offset_increment': treated_results_count,
            'has_more': has_more,
            'progress': json.dumps(next_progress),
        }

    def _get_partner_and_general_ledger_initial_balance_line(self,report, options, parent_line_id, eval_dict, account_currency=None, level_shift=0):
        """ Helper to generate dynamic 'initial balance' lines, used by general ledger and partner ledger.
        """
        line_columns = []
        for column in options['columns']:
            col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
            col_expr_label = column['expression_label']

            if col_value is None or (col_expr_label == 'amount_currency' and not account_currency):
                line_columns.append({})
            else:
                if col_expr_label == 'amount_currency':
                    formatted_value = report.format_value(options, col_value, currency=account_currency, figure_type=column['figure_type'])
                else:
                    formatted_value = report.format_value(options, col_value, figure_type=column['figure_type'])

                line_columns.append({
                    'name': formatted_value,
                    'no_format': col_value,
                    'class': 'number',
                })

        return {
            'id': report._get_generic_line_id(None, None, parent_line_id=parent_line_id, markup='initial'),
            'class': 'o_account_reports_initial_balance',
            'name': _("Initial Balance"),
            'level': 2 + level_shift,
            'parent_id': parent_line_id,
            'columns': line_columns,
        }

    def export_to_xlsx(self, options, response=None):
        # def write_with_colspan(sheet, x, y, value, colspan, style):
        #     if colspan == 1:
        #         sheet.write(y, x, value, style)
        #     else:
        #         sheet.merge_range(y, x, y, x + colspan - 1, value, style)
        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman', 'font_size': 12,'valign':'vcenter','align': 'left', 'text_wrap': True, 'font_color': 'black'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)
        report_id = self.env['account.report'].browse(int(options['report_id']))
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        # format styles
        default_col1_style = {'font_size': 12, 'font_color': 'black','border': True, 'text_wrap': True}
        level_2_style = {'bold': True, 'font_size': 12, 'font_color': 'black','border': True}
        # end format styles
        print_mode_self = report_id.with_context(no_format=True, print_mode=True, prefetch_fields=False)
        print_options = print_mode_self.get_options(previous_options=options)
        lines = report_id._filter_out_folded_children(print_mode_self._get_lines(print_options))
        group_accounts, parent_name = self.get_group_account(lines)
        for parent_id, lines in group_accounts.items():
            y_offset = 0
            sheet = workbook.add_worksheet(parent_name[parent_id])
            sheet.set_column(0, 1, 25)
            sheet.set_column(2, 2, 15)
            sheet.set_column(3, 4, 50)
            sheet.set_column(5, 8, 13)
            account_id = report_id._get_res_id_from_line_id(parent_id, 'account.account')
            y_offset = self.inject_header(workbook, sheet, options, account_id, y_offset)
            res = self.get_format_data_lines(workbook, sheet, report_id, lines, group_accounts, parent_name, y_offset)
            for line in res.values():
                if line['is_bold']:
                    sheet.merge_range(y_offset, 0, y_offset, 2, line['a'] or '', get_format(default_col1_style))
                    sheet.write(y_offset, 3, line['d'] or '', get_format(level_2_style))
                    sheet.write(y_offset, 4, line['e'] or '', get_format(default_col1_style))
                    sheet.write(y_offset, 5, line['1'], get_format(level_2_style,{'align': 'right'}))
                    sheet.write(y_offset, 6, line['2'], get_format(level_2_style,{'align': 'right'}))
                    sheet.write(y_offset, 7, line['3'], get_format(level_2_style,{'align': 'right'}))
                    sheet.write(y_offset, 8, line['4'], get_format(level_2_style,{'align': 'right'}))
                    y_offset +=1
                else:
                    sheet.write(y_offset, 0, line['a'] or '', get_format(default_col1_style))
                    sheet.write(y_offset, 1, line['b'] or '', get_format(default_col1_style))
                    sheet.write(y_offset, 2, line['c'] or '', get_format(default_col1_style))
                    sheet.write(y_offset, 3, line['d'] or '', get_format(default_col1_style))
                    sheet.write(y_offset, 4, line['e'] or '', get_format(default_col1_style))
                    sheet.write(y_offset, 5, line['1'], get_format(default_col1_style,{'align': 'right'}))
                    sheet.write(y_offset, 6, line['2'], get_format(default_col1_style,{'align': 'right'}))
                    sheet.write(y_offset, 7, line['3'], get_format(default_col1_style,{'align': 'right'}))
                    sheet.write(y_offset, 8, line['4'], get_format(default_col1_style,{'align': 'right'}))
                    y_offset +=1
        
        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return {
            'file_name': report_id.get_default_report_filename(options, 'xlsx'),
            'file_content': generated_file,
            'file_type': 'xlsx',
        }
    
    # Header
    def inject_header(self, workbook, sheet, options, account_id, y_offset):
        report_title = {'bold': True, 'font_size': 16, 'text_wrap': True, 'align': 'center'}
        header_format = {'border': True, 'font_size':13, 'align': 'center','valign': 'vcenter', 'text_wrap': True, 'font_color': 'black'}
        sub_title_format = {'font_size': 13, 'text_wrap': True, 'align': 'center','bold': True}
        # date_default_style = {'font_size': 12, 'font_color': 'black', 'num_format': 'yyyy-mm-dd'}
        # default_style = {'font_size': 12, 'font_color': 'black'}
        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman', 'font_size': 12,'valign':'vcenter','align': 'left', 'text_wrap': True, 'font_color': 'black'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)
        company = self.env.company
        sheet.merge_range(y_offset, 0, y_offset, 1, "Đơn vị: " + company.name, get_format({'bold': True}))
        sheet.merge_range(y_offset, 5, y_offset, 8, "Mẫu số S38-DN", get_format({'bold': True, 'align': 'center'}))
        y_offset +=1
        sheet.set_row(y_offset, 25)
        sheet.merge_range(y_offset, 0, y_offset, 1, "Địa chỉ: " + self.get_company_address(company), get_format({'bold': True}))
        sheet.merge_range(y_offset, 5, y_offset, 8, "(Ban hành theo Thông tư số 200/2014/TT-BTC", get_format({'align': 'center'}))
        y_offset +=1
        sheet.merge_range(y_offset, 5, y_offset, 8, "Ngày 22/12/2014 của Bộ Tài chính)", get_format({'align': 'center'}))
        y_offset +=1
        sheet.merge_range(y_offset, 0, y_offset, 8, "SỔ CHI TIẾT CÁC TÀI KHOẢN", get_format(report_title))
        y_offset +=1
        from_date = options['date']['date_from'] if options.get('date') and options['date'].get('date_from') else ''
        to_date = options['date']['date_to'] if options.get('date') and options['date'].get('date_to') else ''
        if from_date:
            from_date_date = datetime.strptime(from_date, "%Y-%m-%d")
            from_date = from_date_date.strftime('%d/%m/%Y')
        if to_date:
            to_date_date = datetime.strptime(to_date, "%Y-%m-%d")
            to_date = to_date_date.strftime('%d/%m/%Y')
        
        sub_title = 'Từ ngày %s đến ngày %s' % (from_date, to_date)
        sheet.merge_range(y_offset, 0, y_offset , 8, sub_title, get_format(sub_title_format))
        y_offset +=1
        if account_id:
            account = self.env['account.account'].browse(account_id)
            sheet.merge_range(y_offset, 0, y_offset, 8, "Tài khoản: " + account.code + " - " + account.name, get_format(sub_title_format))
            y_offset +=1
        sheet.merge_range(y_offset, 0, y_offset, 8, "Loại tiền: VNĐ", get_format({'align': 'right','bold': True, 'italic': True}))
        y_offset +=1
        # Header talble
        sheet.merge_range(y_offset, 0, y_offset +1, 0, "Ngày, tháng ghi sổ", get_format(header_format))
        sheet.merge_range(y_offset, 1, y_offset, 2, "Chứng từ", get_format(header_format))
        sheet.merge_range(y_offset, 3, y_offset +1, 3, "Diễn giải", get_format(header_format))
        sheet.merge_range(y_offset, 4, y_offset +1, 4, "TK đối ứng", get_format(header_format))
        sheet.merge_range(y_offset, 5, y_offset, 6, "Số phát sinh", get_format(header_format))
        sheet.merge_range(y_offset, 7, y_offset, 8, "Số dư", get_format(header_format))
        sheet.write(y_offset +1, 1, "Số hiệu", get_format(header_format))
        sheet.write(y_offset +1, 2, "Ngày, tháng", get_format(header_format))
        sheet.write(y_offset +1, 5, "Nợ", get_format(header_format))
        sheet.write(y_offset +1, 6, "Có", get_format(header_format))
        sheet.write(y_offset +1, 7, "Nợ", get_format(header_format))
        sheet.write(y_offset +1, 8, "Có", get_format(header_format))
        y_offset+=2
        sheet.write(y_offset, 0, "A", get_format(header_format))
        sheet.write(y_offset, 1, "B", get_format(header_format))
        sheet.write(y_offset, 2, "C", get_format(header_format))
        sheet.write(y_offset, 3, "D", get_format(header_format))
        sheet.write(y_offset, 4, "E", get_format(header_format))
        sheet.write(y_offset, 5, "1", get_format(header_format))
        sheet.write(y_offset, 6, "2", get_format(header_format))
        sheet.write(y_offset, 7, "3", get_format(header_format))
        sheet.write(y_offset, 8, "4", get_format(header_format))
        y_offset +=1
        return y_offset

    def get_format_data_lines(self, workbook, sheet, report_id, lines, group_accounts, parent_name, y_offset):
        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman', 'font_size': 12,'valign':'vcenter','align': 'left', 'text_wrap': True, 'font_color': 'black'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)
        res = {}
        col_stt = {
            'date_numbered': 1,
            'number': 2,
            'date': 3,
            'explain': 4,
            'countered_accounts': 5,
            'debit': 6,
            'credit': 7,
            'balance': 8,
            'id': 9,
        }
        sum_debit = sum_credit = 0
        last_balance = 0
        initial = 0
        for line in lines:
            columns = line['columns']
            if line.get("class") == 'o_account_reports_initial_balance' or len(lines) == 1:
                columns = line.get('columns', [])

                initial_balance = columns[7].get('name', 0) or 0
                initial_balance_str = self.format_float_number(abs(initial_balance))
                initial = initial_balance
                # Số dư đầu kỳ
                res[y_offset] = {
                    'a': '- Số dư đầu kỳ',
                    'b': '',
                    'c': '',
                    'd': '',
                    'e': '',
                    '1': '',
                    '2': '',
                    '3': initial_balance > 0 and initial_balance_str or '',
                    '4': initial_balance < 0 and initial_balance_str or '',
                    'is_bold': True
                }
                y_offset +=1
            else:
                if line.get('class', False) in ('total', 'o_account_reports_totals_below_sections'):
                    continue

                if line.get("parent_id", False) in ['sale~~','purchase~~']:
                    continue
                    
                vals = {
                }

                for x, column in enumerate(columns, start=1):
                    cell_type, cell_value = report_id._get_cell_type_value(column)
                    for key, stt in col_stt.items():
                        if stt == x:
                            vals[key] = cell_value

                move_line = line['id'].split('|')[2]
                aml_str = move_line.split('~account.move.line~')[1]
                aml_id = self.env['account.move.line'].browse(int(aml_str))
                move = aml_id.move_id
                if len(move.line_ids) >= 3:
                    another_line = move.line_ids.filtered(lambda x: x.id != aml_id.id)
                    if float(vals['debit'] or 0) > 0 and not any(ed.debit > 0 for ed in another_line):
                        for edeb in another_line:
                            initial = initial + edeb.credit - edeb.debit
                            res[y_offset] = {
                                'a': edeb.date and edeb.date.strftime('%d/%m/%Y') or '',
                                'b': vals['number'],
                                'c': edeb.date and edeb.date.strftime('%d/%m/%Y') or '',
                                'd': edeb.name,
                                'e': edeb.account_id.code,
                                '1': self.format_float_number(edeb.credit),
                                '2': self.format_float_number(edeb.debit),
                                '3': initial > 0 and self.format_float_number(initial) or '',
                                '4': initial < 0 and self.format_float_number(abs(initial)) or '',
                                'is_bold': False
                            }

                            y_offset +=1 
                            sum_debit += edeb.credit
                            sum_credit += edeb.debit

                            last_balance = initial

                        continue

                    if float(vals['credit'] or 0) > 0 and not any(ec.credit > 0 for ec in another_line):
                        for ecre in another_line:
                            initial = initial + ecre.credit - ecre.debit
                            res[y_offset] = {
                                'a': ecre.date and ecre.date.strftime('%d/%m/%Y') or '',
                                'b': vals['number'],
                                'c': ecre.date and ecre.date.strftime('%d/%m/%Y') or '',
                                'd': ecre.name,
                                'e': ecre.account_id.code,
                                '1': self.format_float_number(ecre.credit),
                                '2': self.format_float_number(ecre.debit),
                                '3': initial > 0 and self.format_float_number(initial) or '',
                                '4': initial < 0 and self.format_float_number(abs(initial)) or '',
                                'is_bold': False
                            }

                            y_offset +=1 

                            sum_debit += ecre.credit
                            sum_credit += ecre.debit

                            last_balance = initial

                        continue

                sum_debit += float(vals['debit'] or 0)
                sum_credit += float(vals['credit'] or 0)

                initial = initial + float(vals['debit'] or 0) - float(vals['credit'] or 0)
                last_balance = initial

                res[y_offset] = {
                    'a': vals['date_numbered'],
                    'b': vals['number'],
                    'c': vals['date'] and vals['date'].strftime('%d/%m/%Y') or '',
                    'd': vals['explain'],
                    'e': vals['countered_accounts'],
                    '1': self.format_float_number(vals['debit']),
                    '2': self.format_float_number(vals['credit']),
                    '3': initial > 0 and self.format_float_number(initial) or '',
                    '4': initial < 0 and self.format_float_number(abs(initial)) or '',
                    'is_bold': False
                }
                y_offset += 1
    #     # Cộng số phát sinh
        res[y_offset] = {
            'a': '',
            'b': '',
            'c': '',
            'd': '- Cộng số phát sinh',
            'e': '',
            '1': self.format_float_number(sum_debit),
            '2': self.format_float_number(sum_credit),
            '3': '',
            '4': '',
            'is_bold': True
        }
        y_offset +=1   
        res[y_offset] = {
            'a': '',
            'b': '',
            'c': '',
            'd': '- Số dư cuối kỳ',
            'e': '',
            '1': '',
            '2': '',
            '3': last_balance > 0 and self.format_float_number(abs(last_balance)) or '',
            '4': last_balance < 0 and  self.format_float_number(abs(last_balance)) or '',
            'is_bold': True
        }   
        y_offset +=1    

        # footer
        y_offset +=1
        sheet.merge_range(y_offset, 0, y_offset, 8, '- Sổ này có ... trang, đánh số từ trang 01 đến trang ...', get_format())
        y_offset +=1
        sheet.merge_range(y_offset, 0, y_offset, 8, '- Ngày mở sổ: ...', get_format())
        y_offset +=2
        sheet.merge_range(y_offset, 6, y_offset, 8, 'Ngày .....tháng.....năm........', get_format({'italic': True, 'align': 'center'}))
        y_offset +=1
        sheet.merge_range(y_offset, 0, y_offset, 1, 'Người ghi sổ', get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 3, y_offset, 5, 'Kế toán trưởng', get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 6, y_offset, 8, 'Giám đốc', get_format({'bold': True, 'align': 'center'}))

        y_offset +=1
        sheet.merge_range(y_offset, 0, y_offset, 1, '(Ký, họ tên)', get_format({'italic': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 3, y_offset, 5, '(Ký, họ tên)', get_format({'italic': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 6, y_offset, 8, '(Ký, họ tên, đóng dấu)', get_format({'italic': True, 'align': 'center'}))
        return res

    def _get_accounts(self, options):
        accounts = []
        if options and options.get('account_accounts', False):
            accounts = self.env['account.account'].browse(options.get('account_accounts'))
            accounts = ['%s %s' % (x.code, x.name) for x in accounts]
        return ', '.join(accounts)

    def get_company_address(self, company_id):
        address = ''
        if company_id:
            if company_id.street:
                address = company_id.street
            if company_id.street2:
                address += len(address) and ', ' + company_id.street2 or company_id.street2
            if company_id.city:
                address += len(address) and ', ' + company_id.city or company_id.city
            if company_id.state_id:
                address += len(address) and ', ' + company_id.state_id.name or company_id.state_id.name
            if company_id.country_id:
                address += len(address) and ', ' + company_id.country_id.name or company_id.country_id.name
        return address

    def get_group_account(self, lines):
        group_parent = {}
        parent_name = {}
        for line in lines:
            if line.get('parent_id', False):
                if line['parent_id'] not in group_parent:
                    group_parent[line['parent_id']] = [line]
                else:
                    group_parent[line['parent_id']].append(line)
            else:
                if line.get('class', '') == 'total':
                    continue
                if line['id'] not in group_parent:
                    group_parent[line['id']] = [line]
                if line['id'] not in parent_name:
                    parent_name[line['id']] = line['name']

        return group_parent, parent_name

    def format_float_number(self, num):
        if not num:
            return 0

        number = float(num)
        if number % 1 == 0:
            return "{:,.0f}".format(number)
        else:
            number_format = "{:,.2f}".format(number).rstrip('0')
            numbers = number_format.split('.')
            return numbers[0] + ',' + numbers[1]

    def _get_partners(self, options):
        partners = []
        if options and options.get('partner_ids', False):
            partners = self.env['res.partner'].browse(options.get('partner_ids')).mapped('name')
            partners = [str(x) for x in partners]
        return ','.join(partners)

    def get_format_data_lines_pdf(self, report_id, lines):
        """ Hàm helper xử lý dữ liệu thô từ report line thành cấu trúc dict 
            tương thích hoàn toàn với file template QWeb XML của bạn.
        """
        res = {}
        y_offset = 0
        col_stt = {
            'date_numbered': 1, 'number': 2, 'date': 3, 'explain': 4,
            'countered_accounts': 5, 'debit': 6, 'credit': 7, 'balance': 8, 'id': 9,
        }
        sum_debit = sum_credit = 0
        last_balance = 0
        initial = 0
        
        for line in lines:
            columns = line['columns']
            if line.get("class") == 'o_account_reports_initial_balance' or len(lines) == 1:
                columns = line.get('columns', [])
                initial_balance = columns[7].get('name', 0) or 0
                initial_balance_str = self.format_float_number(abs(initial_balance))
                initial = initial_balance
                
                res[y_offset] = {
                    'a': '- Số dư đầu kỳ', 'b': '', 'c': '', 'd': '', 'e': '', '1': '', '2': '',
                    '3': initial_balance > 0 and initial_balance_str or '',
                    '4': initial_balance < 0 and initial_balance_str or '',
                    'is_bold': True
                }
                y_offset += 1
            else:
                if line.get('class', False) in ('total', 'o_account_reports_totals_below_sections'):
                    continue
                if line.get("parent_id", False) in ['sale~~', 'purchase~~']:
                    continue
                    
                vals = {}
                for x, column in enumerate(columns, start=1):
                    cell_type, cell_value = report_id._get_cell_type_value(column)
                    for key, stt in col_stt.items():
                        if stt == x:
                            vals[key] = cell_value

                # Tách dòng đối ứng giữ nguyên logic gốc của bạn
                move_line = line['id'].split('|')[2]
                aml_str = move_line.split('~account.move.line~')[1]
                aml_id = self.env['account.move.line'].browse(int(aml_str))
                move = aml_id.move_id
                
                if len(move.line_ids) >= 3:
                    another_line = move.line_ids.filtered(lambda x: x.id != aml_id.id)
                    if float(vals.get('debit') or 0) > 0 and not any(ed.debit > 0 for ed in another_line):
                        for edeb in another_line:
                            initial = initial + edeb.credit - edeb.debit
                            res[y_offset] = {
                                'a': edeb.date and edeb.date.strftime('%d/%m/%Y') or '',
                                'b': vals.get('number', ''),
                                'c': edeb.date and edeb.date.strftime('%d/%m/%Y') or '',
                                'd': edeb.name,
                                'e': edeb.account_id.code,
                                '1': self.format_float_number(edeb.credit),
                                '2': self.format_float_number(edeb.debit),
                                '3': initial > 0 and self.format_float_number(initial) or '',
                                '4': initial < 0 and self.format_float_number(abs(initial)) or '',
                                'is_bold': False
                            }
                            y_offset += 1 
                            sum_debit += edeb.credit
                            sum_credit += edeb.debit
                            last_balance = initial
                        continue

                    if float(vals.get('credit') or 0) > 0 and not any(ec.credit > 0 for ec in another_line):
                        for ecre in another_line:
                            initial = initial + ecre.credit - ecre.debit
                            res[y_offset] = {
                                'a': ecre.date and ecre.date.strftime('%d/%m/%Y') or '',
                                'b': vals.get('number', ''),
                                'c': ecre.date and ecre.date.strftime('%d/%m/%Y') or '',
                                'd': ecre.name,
                                'e': ecre.account_id.code,
                                '1': self.format_float_number(ecre.credit),
                                '2': self.format_float_number(ecre.debit),
                                '3': initial > 0 and self.format_float_number(initial) or '',
                                '4': initial < 0 and self.format_float_number(abs(initial)) or '',
                                'is_bold': False
                            }
                            y_offset += 1 
                            sum_debit += ecre.credit
                            sum_credit += ecre.debit
                            last_balance = initial
                        continue

                sum_debit += float(vals.get('debit') or 0)
                sum_credit += float(vals.get('credit') or 0)
                initial = initial + float(vals.get('debit') or 0) - float(vals.get('credit') or 0)
                last_balance = initial

                res[y_offset] = {
                    'a': vals.get('date_numbered', ''),
                    'b': vals.get('number', ''),
                    'c': vals.get('date') and vals.get('date').strftime('%d/%m/%Y') or '',
                    'd': vals.get('explain', ''),
                    'e': vals.get('countered_accounts', ''),
                    '1': self.format_float_number(vals.get('debit')),
                    '2': self.format_float_number(vals.get('credit')),
                    '3': initial > 0 and self.format_float_number(initial) or '',
                    '4': initial < 0 and self.format_float_number(abs(initial)) or '',
                    'is_bold': False
                }
                y_offset += 1

        # Cộng số phát sinh & Số dư cuối kỳ
        res[y_offset] = {
            'a': '', 'b': '', 'c': '', 'd': '- Cộng số phát sinh', 'e': '',
            '1': self.format_float_number(sum_debit), '2': self.format_float_number(sum_credit),
            '3': '', '4': '', 'is_bold': True
        }
        y_offset += 1   
        res[y_offset] = {
            'a': '', 'b': '', 'c': '', 'd': '- Số dư cuối kỳ', 'e': '', '1': '', '2': '',
            '3': last_balance > 0 and self.format_float_number(abs(last_balance)) or '',
            '4': last_balance < 0 and self.format_float_number(abs(last_balance)) or '',
            'is_bold': True
        }   
        return res

    def acction_print_pdf(self, options):
        """ Hàm xử lý in ra file ZIP chứa nhiều file PDF (Đã tối ưu hiệu năng) """
        report_id = self.env['account.report'].browse(int(options['report_id']))
        
        # 1. BẬT CHẾ ĐỘ QUERY TOÀN BỘ DATA 1 LẦN DUY NHẤT
        print_mode_self = report_id.with_context(no_format=True, print_mode=True, prefetch_fields=False)
        print_options = print_mode_self.get_options(previous_options=options)
        print_options['unfold_all'] = True # Đảm bảo mở hết các dòng để lấy đầy đủ chi tiết aml
        
        # Thực hiện câu lệnh SQL duy nhất tại đây
        all_lines = report_id._filter_out_folded_children(print_mode_self._get_lines(print_options))
        
        # Phân tách dữ liệu tổng thành các nhóm theo từng Tài khoản
        group_accounts, parent_name = self.get_group_account(all_lines)
        
        # Khởi tạo tệp nén ZIP trong bộ nhớ bộ đệm
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for parent_id, acc_lines in group_accounts.items():
                acc_name = parent_name.get(parent_id, 'Tai_Khoan')
                
                # Định dạng cấu trúc dữ liệu PDF cho cụm dòng của tài khoản hiện tại
                formatted_lines = self.get_format_data_lines_pdf(report_id, acc_lines)
                
                # Đóng gói dữ liệu tính toán sẵn (Bao gồm cờ hiệu 'is_precomputed')
                pdf_data = {
                    **options,
                    'is_precomputed': True,
                    'precomputed_account_name': acc_name,
                    'precomputed_lines': formatted_lines,
                }
                
                # 2. RENDER PDF (Data đã có sẵn nên Odoo sẽ không cần kết nối DB để tính toán lại nữa)
                report_ref = 'biz_details_of_account_books.action_print_detail_book_pdf'
                pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_ref, res_ids=self.ids, data=pdf_data)
                
                # Xóa các ký tự đặc biệt khỏi tên file tránh lỗi hệ thống file
                clean_acc_name = acc_name.replace('/', '_').replace(' ', '_').replace(':', '_')
                file_name = f"So_Chi_Tiet_TK_{clean_acc_name}.pdf"
                
                # Đưa file vào tệp ZIP
                zip_file.writestr(file_name, pdf_content)

        zip_buffer.seek(0)
        
        # 3. Tạo attachment và trả về Action để trình duyệt tự động tải file xuống
        attachment = self.env['ir.attachment'].create({
            'name': 'So_Chi_Tiet_Cac_Tai_Khoan.zip',
            'type': 'binary',
            'datas': base64.b64encode(zip_buffer.read()),
            'mimetype': 'application/zip',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
            'attachment_id': attachment.id,
        }
