# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import os
import io

from odoo import models, _, fields, api
from odoo.tools import SQL
from datetime import datetime
from collections import defaultdict
from datetime import timedelta
from openpyxl.styles import Alignment, Border, Side, Font
from openpyxl.styles import PatternFill
from openpyxl import load_workbook

_logger = logging.getLogger(__name__)

TRIAL_BALANCE_END_COLUMN_GROUP_KEY = '_trial_balance_end_column_group'


class TrialBalanceVASCustomHandler(models.AbstractModel):
    _name = 'account.trial.balance.vas.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'Trial Balance Custom Handler'

    # PCV customize get line base on VAS (CoA 200)

    def _get_account_title_line(self, report, options, account, has_lines, eval_dict):
        line_columns = []
        for column in options['columns']:
            col_value = eval_dict.get(column['column_group_key'], {}).get(column['expression_label'])
            col_expr_label = column['expression_label']

            value = None if col_value is None or (col_expr_label == 'amount_currency' and not account.currency_id) else col_value

            line_columns.append(report._build_column_dict(
                value,
                column,
                options=options,
                currency=account.currency_id if col_expr_label == 'amount_currency' else None,
            ))

        line_id = report._get_generic_line_id('account.account', account.id)
        is_in_unfolded_lines = any(
            report._get_res_id_from_line_id(line_id, 'account.account') == account.id
            for line_id in options.get('unfolded_lines')
        )
        return {
            'id': line_id,
            'name': account.name,
            'account_code': account.code,
            'columns': line_columns,
            'level': 1,
            'unfoldable': has_lines,
            'unfolded': has_lines and (is_in_unfolded_lines or options.get('unfold_all')),
            'expand_function': '_report_expand_unfoldable_line_general_ledger',
        }

    @api.model
    def _get_total_line(self, report, options, eval_dict):
        line_columns = []
        for column in options['columns']:
            col_value = eval_dict[column['column_group_key']].get(column['expression_label'])
            col_value = None if col_value is None else col_value

            line_columns.append(report._build_column_dict(col_value, column, options=options))
        return {
            'id': report._get_generic_line_id(None, None, markup='total'),
            'name': _('Total'),
            'level': 1,
            'columns': line_columns,
        }

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

        new_options['date'] = self.env['account.report']._get_dates_period(None, new_date_to, 'single')

        return new_options

    def _get_query_sums(self, report, options) -> SQL:
        """ Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :return:                    query as SQL object
        """
        options_by_column_group = report._split_options_per_column_group(options)

        queries = []

        # ============================================
        # 1) Get sums for all accounts.
        # ============================================
        for column_group_key, options_group in options_by_column_group.items():

            # Sum is computed including the initial balance of the accounts configured to do so, unless a special option key is used
            # (this is required for trial balance, which is based on general ledger)
            sum_date_scope = 'strict_range' if options_group.get('general_ledger_strict_range') else 'from_beginning'

            query_domain = []

            if not options_group.get('general_ledger_strict_range'):
                date_from = fields.Date.from_string(options_group['date']['date_from'])
                current_fiscalyear_dates = self.env.company.compute_fiscalyear_dates(date_from)
                query_domain += [
                    '|',
                    ('date', '>=', current_fiscalyear_dates['date_from']),
                    ('account_id.include_initial_balance', '=', True),
                ]

            if options_group.get('export_mode') == 'print' and options_group.get('filter_search_bar'):
                query_domain.append(('account_id', 'ilike', options_group['filter_search_bar']))

            if options_group.get('include_current_year_in_unaff_earnings'):
                query_domain += [('account_id.include_initial_balance', '=', True)]

            query = report._get_report_query(options_group, sum_date_scope, domain=query_domain)
            queries.append(SQL(
                """
                SELECT
                    account_move_line.account_id                            AS groupby,
                    'sum'                                                   AS key,
                    MAX(account_move_line.date)                             AS max_date,
                    %(column_group_key)s                                    AS column_group_key,
                    account_move_line.partner_id                            AS partner_id,
                    COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                    SUM(%(debit_select)s)   AS debit,
                    SUM(%(credit_select)s)  AS credit,
                    SUM(%(balance_select)s) AS balance
                FROM %(table_references)s
                %(currency_table_join)s
                LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
                WHERE %(search_condition)s
                GROUP BY account_move_line.account_id, account_move_line.partner_id
                """,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                currency_table_join=report._currency_table_aml_join(options_group),
                search_condition=query.where_clause,
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
                        account_move_line.partner_id                            AS partner_id,
                        COALESCE(SUM(account_move_line.amount_currency), 0.0)   AS amount_currency,
                        SUM(%(debit_select)s)                                   AS debit,
                        SUM(%(credit_select)s)                                  AS credit,
                        SUM(%(balance_select)s) AS balance
                    FROM %(table_references)s
                    %(currency_table_join)s
                    LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
                    WHERE %(search_condition)s
                    GROUP BY account_move_line.company_id, account_move_line.partner_id
                    """,
                    column_group_key=column_group_key,
                    table_references=query.from_clause,
                    debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                    credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                    balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                    currency_table_join=report._currency_table_aml_join(options_group),
                    search_condition=query.where_clause,
                ))

        return SQL(" UNION ALL ").join(queries)

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
        query, params = self._get_query_sums(report, options)
        if not query:
            return []

        groupby_accounts = {}
        groupby_companies = {}
        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            # No result to aggregate.
            if res['groupby'] is None:
                continue

            column_group_key = res['column_group_key']
            key = res['key']
            ##################################
            # VAS 200: NEED UPDATE
            ########### start ################
            if key == 'sum':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {}
                                            for col_group_key in options['column_groups']})
                partner_id = res.pop('partner_id', None)
                if key not in groupby_accounts[res['groupby']][column_group_key]:
                    res.update({'partner_ids': [{
                        'partner_id': partner_id,
                        'amount_currency': res['amount_currency'],
                        'debit': res['debit'],
                        'credit': res['credit'],
                        'balance': res['balance']}],
                    })
                    groupby_accounts[res['groupby']][column_group_key][key] = res
                else:
                    sum_val = groupby_accounts[res['groupby']][column_group_key][key]
                    for partner_val in sum_val['partner_ids']:
                        # update exisited partner
                        if partner_val['partner_id'] == partner_id:
                            partner_val.update({
                                'amount_currency': partner_val['amount_currency'] + res['amount_currency'],
                                'debit': partner_val['debit'] + res['debit'],
                                'credit': partner_val['credit'] + res['credit'],
                                'balance': partner_val['balance'] + res['balance'],
                            })
                            break
                        need_add_new = True
                    if need_add_new:
                        # add new partner if not exisited
                        sum_val['partner_ids'].append({
                            'partner_id': partner_id,
                            'amount_currency': res['amount_currency'],
                            'debit': res['debit'],
                            'credit': res['credit'],
                            'balance': res['balance'],
                        })
                    groupby_accounts[res['groupby']][column_group_key][key].update({
                        'max_date': res['max_date'] > sum_val['max_date'] and res['max_date'] or sum_val['max_date'],
                        'amount_currency': sum_val['amount_currency'] + res['amount_currency'],
                        'debit': sum_val['debit'] + res['debit'],
                        'credit': sum_val['credit'] + res['credit'],
                        'balance': sum_val['balance'] + res['balance'],
                        'partner_ids': sum_val['partner_ids']
                    })
            # TODO: debug for key in ['initial_balance','unaffected_earnings']
            elif key == 'initial_balance':
                groupby_accounts.setdefault(res['groupby'], {col_group_key: {}
                                            for col_group_key in options['column_groups']})
                groupby_accounts[res['groupby']][column_group_key][key] = res

            elif key == 'unaffected_earnings':
                groupby_companies.setdefault(res['groupby'], {col_group_key: {}
                                             for col_group_key in options['column_groups']})
                groupby_companies[res['groupby']][column_group_key] = res

            ########## end of customize vas 200 ##############
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

    def _vas200_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
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
                # VAS 200 update debit/credit/balance groupby partner if account is follow by partner
                if account.follow_by_partner and ('initial_balance' in column_group_key or 'end_balance' in column_group_key):
                    account_debit = 0.0
                    account_credit = 0.0
                    for partner_val in account_sum.get('partner_ids', []):
                        # tk mang tính chất lưỡng tính hiển thị ở cột có giá trị lớn hơn với công thức là debit - credit
                        amount_in_period = partner_val.get('debit', 0.0) - partner_val.get('credit', 0.0)
                        if amount_in_period >= 0:
                            account_debit += amount_in_period
                        else:
                            account_credit += abs(amount_in_period)
                    account_debit += account_un_earn.get('debit', 0.0)
                    account_credit += account_un_earn.get('credit', 0.0)
                    account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
                else:
                    account_debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
                    account_credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
                    account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

                eval_dict[column_group_key] = {
                    'amount_currency': account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
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

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        def _update_column(line, column_key, new_value):
            line['columns'][column_key]['no_format'] = new_value
            line['columns'][column_key]['is_zero'] = self.env.company.currency_id.is_zero(new_value)

        def _update_balance_columns(line, debit_column_key, credit_column_key):
            debit_value = line['columns'][debit_column_key]['no_format'] if debit_column_key is not None else False
            credit_value = line['columns'][credit_column_key]['no_format'] if credit_column_key is not None else False

            if debit_value and credit_value:
                new_debit_value = 0.0
                new_credit_value = 0.0

                if self.env.company.currency_id.compare_amounts(debit_value, credit_value) == 1:
                    new_debit_value = debit_value - credit_value
                else:
                    new_credit_value = (debit_value - credit_value) * -1

                _update_column(line, debit_column_key, new_debit_value)
                _update_column(line, credit_column_key, new_credit_value)

        lines = [line[1] for line in
            self._vas200_lines_generator(report, options,
                all_column_groups_expression_totals, warnings=warnings)]

        # We need to find the index of debit and credit columns for initial and end balance in case of extra custom columns
        init_balance_debit_index = next(
            (index for index, column in enumerate(options['columns']) if column.get('expression_label') == 'debit'),
            None)
        init_balance_credit_index = next(
            (index for index, column in enumerate(options['columns']) if column.get('expression_label') == 'credit'),
            None)

        end_balance_debit_index = next((index for index, column in enumerate(options['columns']) if
        column.get('expression_label') == 'debit' and column.get(
            'column_group_key') == TRIAL_BALANCE_END_COLUMN_GROUP_KEY), None)
        end_balance_credit_index = next((index for index, column in enumerate(options['columns']) if
        column.get('expression_label') == 'credit' and column.get(
            'column_group_key') == TRIAL_BALANCE_END_COLUMN_GROUP_KEY), None)

        currency = self.env.company.currency_id
        for line in lines[:-1]:
            # Initial balance
            _update_balance_columns(line, init_balance_debit_index, init_balance_credit_index)

            # End balance: sum all the previous columns for both debit and credit
            if end_balance_debit_index is not None:
                end_balance_debit_sum = sum(
                    currency.round(column['no_format'])
                        for index, column in enumerate(line['columns'])
                        if column.get('expression_label') == 'debit' and index != end_balance_debit_index and column[
                        'no_format'] is not None
                )
                _update_column(line, end_balance_debit_index, end_balance_debit_sum)

            if end_balance_credit_index is not None:
                end_balance_credit_sum = sum(
                    currency.round(column['no_format'])
                        for index, column in enumerate(line['columns'])
                        if column.get('expression_label') == 'credit' and index != end_balance_credit_index and column[
                        'no_format'] is not None
                )
                _update_column(line, end_balance_credit_index, end_balance_credit_sum)

            _update_balance_columns(line, end_balance_debit_index, end_balance_credit_index)

            line.pop('expand_function', None)
            line.pop('groupby', None)
            line.update({
                'unfoldable': False,
                'unfolded': False,
            })

            res_model = report._get_model_info_from_id(line['id'])[0]
            if res_model == 'account.account':
                line['caret_options'] = 'trial_balance'

        # Total line
        if lines:
            total_line = lines[-1]

            for index in (
            init_balance_debit_index, init_balance_credit_index, end_balance_debit_index, end_balance_credit_index):
                if index is not None:
                    total_line['columns'][index]['no_format'] = sum(
                        currency.round(line['columns'][index]['no_format']) for line in lines[:-1] if
                        report._get_model_info_from_id(line['id'])[0] == 'account.account')

        return [(0, line) for line in lines]

    def _caret_options_initializer(self):
        # TODO: VAS 200: change action to VAS General Ledger
        return {
            'trial_balance': [
                {'name': _("General Ledger"), 'action': 'caret_option_open_general_ledger'},
                {'name': _("Journal Items"), 'action': 'open_journal_items'},
            ],
        }

    def _get_column_group_creation_data(self, report, options, previous_options=None):
        """
        Return tuple of tuples containing a reference to the column_group creation function and on which side ('left' | 'right') of the report the column_group goes
        """
        return (
            (self._create_column_group_initial_balance, 'left'),
            (self._create_column_group_end_balance, 'right'),
        )

    @api.model
    def _create_and_append_column_group(self, report, options, header_name, forced_options, side_to_append, group_vals, exclude_initial_balance=False, append_col_groups=True):
        header_element = [{'name': header_name, 'forced_options': forced_options}]
        column_headers = [header_element, *options['column_headers'][1:]]
        column_group_vals = report._generate_columns_group_vals_recursively(column_headers, group_vals)

        if exclude_initial_balance:
            # This column group must not include initial balance; we use a special option key for that in general ledger
            for column_group in column_group_vals:
                column_group['forced_options']['general_ledger_strict_range'] = True

        columns, column_groups = report._build_columns_from_column_group_vals(forced_options, column_group_vals)

        side_to_append['column_headers'] += header_element
        if append_col_groups:
            side_to_append['column_groups'] |= column_groups
        side_to_append['columns'] += columns

    def _custom_options_initializer(self, report, options, previous_options):
        """ Modifies the provided options to add a column group for initial balance and end balance, as well as the appropriate columns.
        """
        default_group_vals = {'horizontal_groupby_element': {}, 'forced_options': {}}
        left_side = {'column_headers': [], 'column_groups': {}, 'columns': []}
        right_side = {'column_headers': [], 'column_groups': {}, 'columns': []}

        # Columns between initial and end balance must not include initial balance; we use a special option key for that in general ledger
        for column_group in options['column_groups'].values():
            column_group['forced_options']['general_ledger_strict_range'] = True

        if options.get('comparison') and not options['comparison'].get('periods'):
            options['comparison']['period_order'] = 'ascending'

        # Create column groups
        for function, side in self._get_column_group_creation_data(report, options, previous_options):
            function(report, options, previous_options, default_group_vals, left_side if side == 'left' else right_side)
        # Update options
        options['column_headers'][0] = left_side['column_headers'] + options['column_headers'][0] + right_side['column_headers']
        options['column_groups'].update(left_side['column_groups'])
        options['column_groups'].update(right_side['column_groups'])
        left_side_col = left_side['columns']
        options['columns'] = left_side['columns'] + options['columns'] + right_side['columns']
        options['ignore_totals_below_sections'] = True  # So that GL does not compute them

        # All the periods displayed between initial and end balance need to use the same rates, so we manually change the period key.
        # account.report will then compute the currency table periods accordingly
        middle_periods_period_key = '_trial_balance_middle_periods'
        for col_group in options['column_groups'].values():
            col_group_date = col_group['forced_options'].get('date')
            if col_group_date:
                col_group_date['currency_table_period_key'] = middle_periods_period_key

        report._init_options_order_column(options, previous_options)

    def _custom_line_postprocessor(self, report, options, lines, warnings=None):
        # If the hierarchy is enabled, ensure to add the o_account_coa_column_contrast class to the hierarchy lines
        if options.get('hierarchy'):
            for line in lines:
                model, dummy = report._get_model_info_from_id(line['id'])
                if model == 'account.group':
                    line_classes = line.get('class', '')
                    line['class'] = line_classes + ' o_account_coa_column_contrast_hierarchy'
                    # customize debit/credit of group
                    eval_dict = {}
                    for column in line['columns']:
                        if column['column_group_key'] not in eval_dict:
                            eval_dict[column['column_group_key']] = {
                                column['expression_label']: float(column['no_format'])
                            }
                        else:
                            eval_dict[column['column_group_key']].update({
                                column['expression_label']: float(column['no_format'])
                            })
                    # for column_group, dict_val in eval_dict.items():
                    #     if 'initial_balance' in column_group or 'end_balance' in column_group:
                    #         balance = dict_val.get('debit', 0.0) - dict_val.get('credit', 0.0)
                    #         expr_label = 'debit' if balance > 0 else 'credit'
                    #         for col in filter(lambda x: x['column_group_key'] == column_group, line['columns']):
                    #             if col['expression_label'] == expr_label:
                    #                 col.update({
                    #                     'no_format': balance > 0 and balance or balance * -1,
                    #                     'name': report.format_value(
                    #                         options,
                    #                         balance > 0 and balance or balance * -1,
                    #                         currency=col.get('currency'),
                    #                         blank_if_zero=col.get('blank_if_zero'),
                    #                         figure_type=col.get('figure_type'),
                    #                         digits=col.get('digits'))
                    #                 })
                    #             else:
                    #                 col.update({
                    #                     'no_format': 0.0,
                    #                     'name': 0
                    #                 })
        return lines

    def _create_column_group_initial_balance(self, report, options, previous_options, default_group_vals, side_to_append):
        initial_balance_options = self.env['account.general.ledger.report.handler']._get_options_initial_balance(options)
        initial_forced_options = {
            'date': initial_balance_options['date'],
            'include_current_year_in_unaff_earnings': initial_balance_options['include_current_year_in_unaff_earnings'],
            'no_impact_on_currency_table': True,
        }
        self._create_and_append_column_group(
            report,
            options,
            _("Initial Balance"),
            initial_forced_options,
            side_to_append,
            default_group_vals,
        )

    def _create_column_group_end_balance(self, report, options, previous_options, default_group_vals, side_to_append):
        end_date_to = options['date']['date_to']
        end_date_from = options['comparison']['periods'][-1]['date_from'] if options.get('comparison', {}).get('periods') else options['date']['date_from']
        end_forced_options = {
            'date': report._get_dates_period(
                fields.Date.from_string(end_date_from),
                fields.Date.from_string(end_date_to),
                'range',
            ),
        }
        self._create_and_append_column_group(
            report,
            options,
            _("End Balance"),
            end_forced_options,
            side_to_append,
            default_group_vals,
            append_col_groups=False,
        )

        # We don't add end_column_groups on purpose: they shouldn't be computed, since we'll just sum the values of other groups in that one.
        # So, we don't want to run any SQL for it. We also force a dedicated column_group_key on the end columns, to better identify them.
        for column_data in side_to_append['columns'][-len(report.column_ids):]:
            column_data['column_group_key'] = TRIAL_BALANCE_END_COLUMN_GROUP_KEY


    def export_to_xlsx(self, options, response=None):
        report_id = self.env.ref('pcv_vas_trial_balance_report.vas_trial_balance_report')
        report_lines = report_id.get_report_information(options)['lines']
        col_amount_title = ['opening_debit', 'opening_credit',
                            'arising_debit', 'arising_credit', 'closing_debit', 'closing_credit']
        report_line_for_excel = []
        for line in report_lines:
            temp = {}
            columns = line.get('columns', [])
            for index, value in enumerate(columns):
                temp[col_amount_title[index]] = value['no_format']
            # code, name = [line['name'].split()[0]] + [' '.join(line['name'].split()[1:])]
            # if not code.startswith("N") and not code.isdigit():
            #     name = line['name']
            #     code = ''
            name = line.get('name')
            if line.get('name') == 'Total':
                name = 'Tổng cộng'
            temp['is_root'] = 'account.account' not in line.get('id')

            temp['line_name'] = name
            temp['account_code'] = line.get('account_code', '')
            report_line_for_excel.append(temp)
        return self.write_report_lines_into_excel(report_line_for_excel, options['date'])

    def write_report_lines_into_excel(self, report_lines, date_range):
        for i in ['date_from', 'date_to']:
            date_range[i] = datetime.strptime(date_range.get(i, '1990-01-01'), "%Y-%m-%d")
        account_codes = [line.get('account_code') for line in report_lines]
        duplicates = [code for code in account_codes if account_codes.count(code) > 1]
        non_unique_account_codes = list(set(duplicates))

        custom_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        template_file_path = f"{custom_path}/static/report_templates/trial_balance_template.xlsx"

        # region write data
        company = self.env.company
        company_address = ', '.join(
            i for i in [company.street, company.street2, company.city, company.state_id.name, company.country_id.name]
            if i)

        wb = load_workbook(template_file_path)
        ws = wb.active

        # write data not in table
        exclude_table_values = {
            'company_name': {
                'col': 1,  # col A1
                'row': 1,
                'value': f"Công ty: {company.display_name}",
            },
            'company_address': {
                'col': 1,  # col A2
                'row': 2,
                'value': f"Địa chỉ: {company_address}",
            },
            'form_no': {
                'col': 6,  # col F1
                'row': 1,
                'value': 'Mẫu số: S06 - DN',
                'is_center': True
            },
            'info_part_1': {
                'col': 6,  # col F2
                'row': 2,
                'value': '(Ban hành theo Thông tư số 200/2014/TT-BTC',
                'is_center': True
            },
            'info_part_2': {
                'col': 6,  # col F3
                'row': 3,
                'value': 'Ngày 22/12/2014 của Bộ Tài chính)',
                'is_center': True
            },
            'title': {
                'col': 1,  # col A5
                'row': 5,
                'value': f"BẢNG CÂN ĐỐI SỐ PHÁT SINH",
                'is_center': True
            },
            'date': {
                'col': 1,  # col A6
                'row': 6,
                'value': f"Từ ngày {date_range.get('date_from').strftime('%d-%m-%Y')} đến ngày {date_range.get('date_to').strftime('%d-%m-%Y')}",
                'is_center': True
            },

        }

        for key, row in exclude_table_values.items():
            cell = ws.cell(row=row['row'], column=row['col'])
            cell.value = row['value']
            self.css_cell_text(cell, text_center=row.get('text_center', False))
        # write move line row
        table_row = 11  # start from row 11
        index_row = 1

        move_lines_data = report_lines
        row_lst = [
            'account_code', 'line_name', 'opening_debit', 'opening_credit', 'arising_debit',
            'arising_credit', 'closing_debit', 'closing_credit']
        # print(move_lines_data)
        grey_medium = Side(border_style="medium", color="A6A6A6")
        black_medium = Side(border_style="medium", color="000000")
        for row in move_lines_data:
            current_code = row.get('account_code')
            if current_code in non_unique_account_codes and row.get('is_root', False):
                continue
            for col_index, col_name in enumerate(row_lst):
                cell = ws.cell(row=table_row, column=col_index + 1)
                cell.value = row.get(col_name, '')
                # css for cell
                if col_name in ['opening_credit', 'opening_debit',
                                'arising_credit', 'arising_debit', 'closing_credit', 'closing_debit']:
                    cell.number_format = '#,##0'
                if col_index < len(row_lst) - 1:
                    cell.border = Border(top=grey_medium, left=grey_medium, right=grey_medium, bottom=grey_medium)
                else:
                    cell.border = Border(top=grey_medium, left=grey_medium, right=black_medium, bottom=grey_medium)
                cell.font = Font(name='Times New Roman')
                if row.get('is_root', False):
                    self.css_cell_text(cell, bold=True, background_color='FDF5E6')
                else:
                    self.css_cell_text(cell, background_color='FFFFFF')
                if row.get('line_name', '') == 'Tổng cộng':
                    self.css_cell_text(cell, bold=True, background_color='FAFAD2')

            # increase num and index of row
            index_row += 1
            table_row += 1

        # journal date
        journal_row = table_row + 1
        open_journal_date = "Ngày: .............................."
        ws.merge_cells(start_row=journal_row, start_column=6, end_row=journal_row, end_column=8)
        cell = ws.cell(row=journal_row, column=6)
        cell.value = open_journal_date
        cell.font = Font(name='Times New Roman')

        # sign region
        sign_row = journal_row + 2
        sign_rows = [
            {
                'value': 'Người lập biểu',  # A33-B33
                'row': sign_row,
                'col': 1,
                'bold': True,
                'merge_add': 1
            },
            {
                'value': '(Ký, họ tên)',  # A34-B44
                'row': sign_row + 1,
                'col': 1,
                'merge_add': 1
            },
            {
                'value': 'Kế toán trưởng',  # C33
                'row': sign_row,
                'col': 3,
                'bold': True,
                'merge_add': 2
            },
            {
                'value': '(Ký, họ tên)',  # C34
                'row': sign_row + 1,
                'col': 3,
                'merge_add': 2
            },
            {
                'value': 'Người đại diện theo pháp luật',  # F33
                'row': sign_row,
                'col': 6,
                'bold': True,
                'merge_add': 2,
            },
            {
                'value': '(Ký, họ tên)',  # F34
                'row': sign_row + 1,
                'col': 6,
                'merge_add': 2,
            },
        ]

        for sign in sign_rows:
            cell = ws.cell(row=sign['row'], column=sign['col'])

            cell.font = Font(name='Times New Roman')
            self.css_cell_text(cell, text_center=True)
            if sign.get('bold'):
                self.css_cell_text(cell, bold=True)
            if sign.get('italic'):
                self.css_cell_text(cell, italic=True)

            merge_add = sign.get('merge_add')
            if merge_add:
                ws.merge_cells(start_row=sign['row'],
                               start_column=sign['col'], end_row=sign['row'], end_column=sign['col'] + merge_add)
            try:
                cell.value = sign['value']
            except:
                pass
        # # endregion

        # # save and return file
        filename_url = (f"trial_balance_"
                        f"from_{date_range.get('date_from').strftime('%d%m%Y')}_to_{date_range.get('date_to').strftime('%d%m%Y')}.xlsx")
        fp = io.BytesIO()
        wb.save(fp)

        return {
            'file_name': filename_url,
            'file_content': fp.getvalue(),
            'file_type': 'xlsx',
        }

    def css_cell_text(self, cell, text_center=False, bold=False, italic=False, background_color=False):
        if text_center:
            cell.alignment = Alignment(horizontal='center', vertical='center')
        if bold:
            cell.font = Font(name='Times New Roman', bold=True)
        if italic:
            cell.font = Font(name='Times New Roman', italic=True)
        if background_color:
            cell.fill = PatternFill(start_color=background_color, fill_type="solid")
