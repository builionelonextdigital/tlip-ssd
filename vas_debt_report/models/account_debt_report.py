# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, _, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from collections import defaultdict
from openpyxl.styles import Alignment, Border, Side, Font
from openpyxl.styles import PatternFill
from openpyxl import load_workbook
import io
import os
from datetime import datetime
from odoo.tools import SQL


class AccountReport(models.Model):
    _inherit = 'account.report'

    # def _get_filter_account_accounts(self, options, additional_domain=None):
    #     # Method deprecated
    #     report_expected = self.env.ref('vas_debt_report.account_debt_report_data')
    #     if not report_expected or self != report_expected:
    #         return super(AccountReport, self)._get_filter_account_accounts(options, additional_domain)
    #     return self.env['account.account'].with_context(active_test=False).search([
    #         *self.env['account.account']._check_company_domain(self.get_report_company_ids(options)),
    #         *([('follow_by_partner', '=', True)]),
    #     ], order="company_id, name")


class DebtReportCustomHandler(models.AbstractModel):
    _name = 'account.debt.report.handler'
    # _inherit = 'account.report.custom.handler'
    _inherit = 'account.partner.ledger.report.handler'
    _description = 'Accounting Debt Report Custom Handler'

    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        rslt = {partner_id: [] for partner_id in partner_ids}

        partner_ids_wo_none = [x for x in partner_ids if x]
        directly_linked_aml_partner_clauses = []
        indirectly_linked_aml_partner_clause = SQL('aml_with_partner.partner_id IS NOT NULL')
        if None in partner_ids:
            directly_linked_aml_partner_clauses.append(SQL('account_move_line.partner_id IS NULL'))
        if partner_ids_wo_none:
            directly_linked_aml_partner_clauses.append(SQL('account_move_line.partner_id IN %s', tuple(partner_ids_wo_none)))
            indirectly_linked_aml_partner_clause = SQL('aml_with_partner.partner_id IN %s', tuple(partner_ids_wo_none))
        directly_linked_aml_partner_clause = SQL('(%s)', SQL(' OR ').join(directly_linked_aml_partner_clauses))

        queries = []
        journal_name = self.env['account.journal']._field_to_sql('journal', 'name')
        report = self.env.ref('account_reports.partner_ledger_report')
        additional_columns = self._get_additional_column_aml_values()
        domain_param = [
            ('currency_id', '=', self.env.company.currency_id.id),
            # ('currency_id', '!=', False),
            ('account_id.follow_by_partner', '=', True)
        ]
        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(group_options, 'strict_range', domain=domain_param)
            account_alias = query.left_join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')

            # For the move lines directly linked to this partner
            # ruff: noqa: FURB113
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    %(additional_columns)s
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    %(debit_select)s                                                 AS debit,
                    %(credit_select)s                                                AS credit,
                    %(balance_select)s                                               AS amount,
                    %(balance_select)s                                               AS balance,
                    account_move.name                                                AS move_name,
                    account_move.move_type                                           AS move_type,
                    %(account_code)s                                                 AS account_code,
                    %(account_name)s                                                 AS account_name,
                    journal.code                                                     AS journal_code,
                    %(journal_name)s                                                 AS journal_name,
                    %(column_group_key)s                                             AS column_group_key,
                    'directly_linked_aml'                                            AS key,
                    0                                                                AS partial_id
                FROM %(table_references)s
                JOIN account_move ON account_move.id = account_move_line.move_id
                %(currency_table_join)s
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                WHERE %(search_condition)s AND %(directly_linked_aml_partner_clause)s
                ORDER BY account_move_line.date, account_move_line.id
                ''',
                additional_columns=additional_columns,
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                search_condition=query.where_clause,
                directly_linked_aml_partner_clause=directly_linked_aml_partner_clause,
            ))

            # For the move lines linked to no partner, but reconciled with this partner. They will appear in grey in the report
            queries.append(SQL(
                '''
                SELECT
                    account_move_line.id,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    aml_with_partner.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    %(additional_columns)s
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    %(debit_select)s                                                 AS debit,
                    %(credit_select)s                                                AS credit,
                    %(balance_select)s                                               AS amount,
                    %(balance_select)s                                               AS balance,
                    account_move.name                                                AS move_name,
                    account_move.move_type                                           AS move_type,
                    %(account_code)s                                                 AS account_code,
                    %(account_name)s                                                 AS account_name,
                    journal.code                                                     AS journal_code,
                    %(journal_name)s                                                 AS journal_name,
                    %(column_group_key)s                                             AS column_group_key,
                    'indirectly_linked_aml'                                          AS key,
                    partial.id                                                       AS partial_id
                FROM %(table_references)s
                    %(currency_table_join)s,
                    account_partial_reconcile partial,
                    account_move,
                    account_move_line aml_with_partner,
                    account_journal journal
                WHERE
                    (account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id)
                    AND account_move_line.partner_id IS NULL
                    AND account_move.id = account_move_line.move_id
                    AND (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                    AND %(indirectly_linked_aml_partner_clause)s
                    AND journal.id = account_move_line.journal_id
                    AND %(account_alias)s.id = account_move_line.account_id
                    AND %(search_condition)s
                    AND partial.max_date BETWEEN %(date_from)s AND %(date_to)s
                ORDER BY account_move_line.date, account_move_line.id
                ''',
                additional_columns=additional_columns,
                debit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE partial.amount END")),
                credit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE partial.amount END")),
                balance_select=report._currency_table_apply_rate(SQL("-SIGN(aml_with_partner.balance) * partial.amount")),
                account_code=account_code,
                account_name=account_name,
                journal_name=journal_name,
                column_group_key=column_group_key,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(group_options),
                indirectly_linked_aml_partner_clause=indirectly_linked_aml_partner_clause,
                account_alias=SQL.identifier(account_alias),
                search_condition=query.where_clause,
                date_from=group_options['date']['date_from'],
                date_to=group_options['date']['date_to'],
            ))

        query = SQL(" UNION ALL ").join(SQL("(%s)", query) for query in queries)

        if offset:
            query = SQL('%s OFFSET %s ', query, offset)

        if limit:
            query = SQL('%s LIMIT %s ', query, limit)

        self._cr.execute(query)
        for aml_result in self._cr.dictfetchall():
            if aml_result['key'] == 'indirectly_linked_aml':

                # Append the line to the partner found through the reconciliation.
                if aml_result['partner_id'] in rslt:
                    rslt[aml_result['partner_id']].append(aml_result)

                # Balance it with an additional line in the Unknown Partner section but having reversed amounts.
                if None in rslt:
                    rslt[None].append({
                        **aml_result,
                        'debit': aml_result['credit'],
                        'credit': aml_result['debit'],
                        'amount': aml_result['credit'] - aml_result['debit'],
                        'balance': -aml_result['balance'],
                    })
            else:
                rslt[aml_result['partner_id']].append(aml_result)

        return rslt

    @api.model
    def _format_aml_name(self, line_name, move_ref, move_name=None):
        ''' Format the display of an account.move.line record. As its very costly to fetch the account.move.line
        records, only line_name, move_ref, move_name are passed as parameters to deal with sql-queries more easily.

        :param line_name:   The name of the account.move.line record.
        :param move_ref:    The reference of the account.move record.
        :param move_name:   The name of the account.move record.
        :return:            The formatted name of the account.move.line record.
        '''
        names = []
        if move_name is not None and move_name != '/':
            names.append(move_name)
        name = ' - '.join(names)
        return name

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group,
            level_shift=0):
        if aml_query_result['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move.line'

        columns = []
        report = self.env['account.report'].browse(options['report_id'])

        for column in options['columns']:
            col_expr_label = column['expression_label']
            col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result[
                'column_group_key'] else None

            if col_value is None:
                columns.append(report._build_column_debt_dict(None, None))
            else:
                currency = self.env['res.currency'].browse(aml_query_result['currency_id'])

                if col_expr_label == 'balance':
                    col_value += init_bal_by_col_group[column['column_group_key']]
                column['figure_type'] = 'monetary'
                columns.append(
                    report._build_column_debt_dict(col_value, column, options=options, currency=currency))
        return {
            'id': report._get_generic_line_id('account.move.line', aml_query_result['id'],
                parent_line_id=partner_line_id, markup=aml_query_result['partial_id']),
            'parent_id': partner_line_id,
            'name': self._format_aml_name(aml_query_result['name'], aml_query_result['ref'],
                aml_query_result['move_name']),
            'columns': columns,
            'caret_options': caret_type,
            'level': 3 + level_shift,
            'aml_id': aml_query_result['id'],
            'partner_id': aml_query_result['partner_id']
        }

    def _report_expand_unfoldable_line_partner_ledger(self, line_dict_id, groupby, options, progress, offset,
            unfold_all_batch_data=None):
        def init_load_more_progress(line_dict):
            return {
                column['column_group_key']: line_col.get('no_format', 0)
                for column, line_col in zip(options['columns'], line_dict['columns'])
                if column['expression_label'] == 'balance'
            }

        report = self.env.ref('vas_debt_report.account_debt_report_data')
        markup, model, record_id = report._parse_line_id(line_dict_id)[-1]

        if model != 'res.partner':
            raise UserError(_("Wrong ID for partner ledger line to expand: %s", line_dict_id))

        prefix_groups_count = 0
        for markup, dummy1, dummy2 in report._parse_line_id(line_dict_id):
            if markup.startswith('groupby_prefix_group:'):
                prefix_groups_count += 1
        level_shift = prefix_groups_count * 2

        lines = []

        limit_to_load = report.load_more_limit + 1 if report.load_more_limit and options[
            'export_mode'] != 'print' else None

        if unfold_all_batch_data:
            aml_results = unfold_all_batch_data['aml_values'][record_id]
        else:
            aml_results = self._get_aml_values(options, [record_id], offset=offset, limit=limit_to_load)[record_id]

        has_more = False
        treated_results_count = 0
        next_progress = progress
        for result in aml_results:
            if options[
                'export_mode'] != 'print' and report.load_more_limit and treated_results_count == report.load_more_limit:
                # We loaded one more than the limit on purpose: this way we know we need a "load more" line
                has_more = True
                break

            new_line = self._get_report_line_move_line(options, result, line_dict_id, next_progress,
                level_shift=level_shift)

            def line_duplicate(l):
                if l['aml_id'] == result['id']:
                    return True
                else:
                    return False

            old_line = list(filter(line_duplicate, lines))
            if old_line:
                new_line = self._update_report_line_move_line(old_line[0], new_line)
                lines.remove(old_line[0])

            lines.append(new_line)

            next_progress = init_load_more_progress(new_line)
            treated_results_count += 1

        return {
            'lines': lines,
            'offset_increment': treated_results_count,
            'has_more': has_more,
            'progress': next_progress
        }

    def _get_query_sums(self, options) -> SQL:
        """ Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all partners.
        - sums for the initial balances.
        :param options:             The report options.
        :return:                    query as SQL object
        """
        queries = []
        report = self.env.ref('vas_debt_report.account_debt_report_data')
        domain_param = [
            # ('currency_id', '!=', self.env.company.currency_id.id),
            ('currency_id', '!=', False),
            ('account_id.follow_by_partner', '=', True)
        ]
        # Create the currency table.
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(column_group_options, 'strict_range', domain=domain_param)
            queries.append(SQL(
                """
                SELECT
                    account_move_line.partner_id  AS groupby,
                    account_move_line.currency_id AS currency_id,
                    %(column_group_key)s          AS column_group_key,
                    SUM(%(debit_select)s)         AS debit,
                    SUM(%(credit_select)s)        AS credit,
                    SUM(%(balance_select)s)       AS amount,
                    SUM(%(balance_select)s)       AS balance
                FROM %(table_references)s
                %(currency_table_join)s
                WHERE %(search_condition)s AND account_move_line.debit !=0
                GROUP BY account_move_line.partner_id, account_move_line.currency_id
                UNION ALL
                SELECT
                    account_move_line.partner_id  AS groupby,
                    account_move_line.currency_id AS currency_id,
                    %(column_group_key)s          AS column_group_key,
                    SUM(%(debit_select)s)         AS debit,
                    SUM(%(credit_select)s)        AS credit,
                    SUM(%(balance_select)s)       AS amount,
                    SUM(%(balance_select)s)       AS balance
                FROM %(table_references)s
                %(currency_table_join)s
                WHERE %(search_condition)s AND account_move_line.credit !=0
                GROUP BY account_move_line.partner_id, account_move_line.currency_id
                """,
                column_group_key=column_group_key,
                debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
                credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(column_group_options),
                search_condition=query.where_clause,
            ))

        return SQL(' UNION ALL ').join(queries)

    def _query_partners(self, options):
        """ Executes the queries and performs all the computation.
        :return:        A list of tuple (partner, column_group_values) sorted by the table's model _order:
                        - partner is a res.parter record.
                        - column_group_values is a dict(column_group_key, fetched_values), where
                            - column_group_key is a string identifying a column group, like in options['column_groups']
                            - fetched_values is a dictionary containing:
                                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                                - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        """

        def assign_sum(row):
            fields_to_assign = ['balance', 'debit', 'credit']
            if any(not company_currency.is_zero(row[field]) for field in fields_to_assign):
                groupby_partners.setdefault(row['groupby'], defaultdict(lambda: defaultdict(float)))
                for field in fields_to_assign:
                    groupby_partners[row['groupby']][row['column_group_key']][field] += row[field]
                    # groupby_partners[row['groupby']][row['column_group_key']]['currency_id'] = row['currency_id']

        company_currency = self.env.company.currency_id

        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options)

        groupby_partners = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            assign_sum(res)

        # Correct the sums per partner, for the lines without partner reconciled with a line having a partner
        query, params = self._get_sums_without_partner(options)

        self._cr.execute(query, params)
        totals = {}
        for total_field in ['balance', 'debit', 'credit']:
            totals[total_field] = {col_group_key: 0 for col_group_key in options['column_groups']}

        for row in self._cr.dictfetchall():
            totals['debit'][row['column_group_key']] += row.get('debit', 0.0)
            totals['credit'][row['column_group_key']] += row.get('credit', 0.0)
            totals['balance'][row['column_group_key']] += row.get('balance', 0.0)

            if row['groupby'] not in groupby_partners:
                continue

            assign_sum(row)

        if None in groupby_partners:
            # Debit/credit are inverted for the unknown partner as the computation is made regarding the balance of the known partner
            for column_group_key in options['column_groups']:
                groupby_partners[None][column_group_key]['debit'] += totals['credit'][column_group_key]
                groupby_partners[None][column_group_key]['credit'] += totals['debit'][column_group_key]
                groupby_partners[None][column_group_key]['balance'] -= totals['balance'][column_group_key]

        # Retrieve the partners to browse.
        # groupby_partners.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        if groupby_partners:
            # Note a search is done instead of a browse to preserve the table ordering.
            partners = self.env['res.partner'].with_context(active_test=False).search_fetch(
                [('id', 'in', list(groupby_partners.keys()))], ["id", "name", "trust", "company_registry", "vat"])
        else:
            partners = []

        # Add 'Partner Unknown' if needed
        if None in groupby_partners.keys():
            partners = [p for p in partners] + [None]
        return [(partner, groupby_partners[partner.id if partner else None]) for partner in partners]

    def _build_partner_lines(self, report, options, level_shift=0):
        lines = []

        totals_by_column_group = {
            column_group_key: {
                total: 0.0
                for total in ['debit', 'credit', 'balance']
            }
            for column_group_key in options['column_groups']
        }

        partners_results = self._query_partners(options)

        for partner, results in partners_results:
            partner_values = defaultdict(dict)

            # get initial credit & debit
            init_vals = {
                value: 0.0
                for value in ['debit', 'credit', 'balance']
            }
            mid_vals = {
                value: 0.0
                for value in ['debit', 'credit', 'balance']
            }
            end_vals = {
                value: 0.0
                for value in ['debit', 'credit', 'balance']
            }
            # prepare key
            for column_group_key in options['column_groups']:
                if ('initial_balance' in column_group_key):
                    init_vals.update({'key': column_group_key})
                elif ('end_balance' in column_group_key):
                    end_vals.update({'key': column_group_key})
                else:
                    mid_vals.update({'key': column_group_key})

            for col_group_key, col_group_val in results.items():
                if ('initial_balance' in col_group_key):
                    init_vals.update(
                        {
                            'debit': col_group_val.get('debit', 0.0),
                            'credit': col_group_val.get('credit', 0.0),
                            'balance': col_group_val.get('balance', 0.0),
                            'key': col_group_key,
                        }
                    )
                elif ('end_balance' in col_group_key):
                    end_vals['key'] = col_group_key
                else:
                    mid_vals.update(
                        {
                            'debit': col_group_val.get('debit', 0.0),
                            'credit': col_group_val.get('credit', 0.0),
                            'balance': col_group_val.get('balance', 0.0),
                            'key': col_group_key,
                        }
                    )

            # Đầu kỳ
            init_balance = init_vals['debit'] - init_vals['credit']
            if init_vals.get('key', False):
                if init_balance > 0:
                    results[init_vals['key']]['debit'] = init_balance
                    results[init_vals['key']]['credit'] = 0.0
                else:
                    results[init_vals['key']]['debit'] = 0.0
                    results[init_vals['key']]['credit'] = abs(init_balance)
            # Cuối kỳ
            end_balance = (init_vals['debit'] + mid_vals['debit']) - (init_vals['credit'] + mid_vals['credit'])
            if end_balance > 0:
                end_vals['debit'] = end_balance
                end_vals['credit'] = 0.0
            else:
                end_vals['debit'] = 0.0
                end_vals['credit'] = abs(end_balance)

            # End value
            results[end_vals['key']]['debit'] = end_vals['debit']
            results[end_vals['key']]['credit'] = end_vals['credit']

            for column_group_key in options['column_groups']:
                partner_sum = results.get(column_group_key, {})

                partner_values[column_group_key]['debit'] = partner_sum.get('debit', 0.0)
                partner_values[column_group_key]['credit'] = partner_sum.get('credit', 0.0)
                partner_values[column_group_key]['balance'] = partner_sum.get('balance', 0.0)

                totals_by_column_group[column_group_key]['debit'] += partner_values[column_group_key]['debit']
                totals_by_column_group[column_group_key]['credit'] += partner_values[column_group_key]['credit']
                totals_by_column_group[column_group_key]['balance'] += partner_values[column_group_key]['balance']

            lines.append(self._get_report_line_partners(options, partner, partner_values, level_shift=level_shift))
        return lines, totals_by_column_group

    def _get_report_line_partners(self, options, partner, partner_values, level_shift=0):
        company_currency = self.env.company.currency_id

        unfoldable = False
        column_values = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_expr_label = column['expression_label']
            value = partner_values[column['column_group_key']].get(col_expr_label)
            unfoldable = unfoldable or (col_expr_label in ('debit', 'credit') and not company_currency.is_zero(value))
            currency_id = partner_values[column['column_group_key']].get('currency_id', False)
            column_values.append(report._build_column_debt_dict(value, column, options=options,
                currency=self.env['res.currency'].browse(currency_id)))

        line_id = report._get_generic_line_id('res.partner', partner.id) if partner else report._get_generic_line_id(
            'res.partner', None, markup='no_partner')

        return {
            'id': line_id,
            'name': partner is not None and (partner.name or '')[:128] or self._get_no_partner_line_label(),
            'columns': column_values,
            'level': 1 + level_shift,
            'trust': partner.trust if partner else None,
            'unfoldable': unfoldable,
            'unfolded': line_id in options['unfolded_lines'] or options['unfold_all'],
            'expand_function': '_report_expand_unfoldable_line_partner_ledger',
            'partner_id': partner and partner.id or False
        }

    def _get_report_line_total(self, options, totals_by_column_group):
        column_values = []
        report = self.env['account.report'].browse(options['report_id'])
        for column in options['columns']:
            col_value = totals_by_column_group[column['column_group_key']].get(column['expression_label'])
            # column['figure_type'] = 'integer'
            column_values.append(report._build_column_debt_dict(col_value, column, options=options))

        return {
            'id': report._get_generic_line_id(None, None, markup='total'),
            'name': _('Total'),
            'level': 1,
            'columns': column_values,
        }

    def _custom_options_initializer(self, report, options, previous_options=None):
        """ Modifies the provided options to add a column group for initial balance and end balance, as well as the appropriate columns.
        """
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        default_group_vals = {'horizontal_groupby_element': {}, 'forced_options': {}}

        # Columns between initial and end balance must not include initial balance; we use a special option key for that in general ledger
        for column_group in options['column_groups'].values():
            column_group['forced_options']['general_ledger_strict_range'] = True

        if options['comparison']['periods']:
            # Reverse the order the group of columns with the same column_group_key while keeping the original order inside the group
            new_columns_order = []
            current_column = []
            current_column_group_key = options['columns'][-1]['column_group_key']

            for column in reversed(options['columns']):
                if current_column_group_key != column['column_group_key']:
                    current_column_group_key = column['column_group_key']
                    new_columns_order += current_column
                    current_column = []

                current_column.insert(0, column)
            new_columns_order += current_column

            options['columns'] = new_columns_order
            options['column_headers'][0][:] = reversed(options['column_headers'][0])

        # Initial balance
        initial_balance_options = self.env['account.general.ledger.report.handler']._get_options_initial_balance(
            options)
        initial_forced_options = {
            'date': initial_balance_options['date'],
            'initial_balance': True,
            'include_current_year_in_unaff_earnings': initial_balance_options['include_current_year_in_unaff_earnings']
        }
        initial_header_element = [{'name': _("Initial Balance"), 'forced_options': initial_forced_options}]
        col_headers_initial = [
            initial_header_element,
            *options['column_headers'][1:],
        ]
        initial_column_group_vals = report._generate_columns_group_vals_recursively(
            col_headers_initial, default_group_vals)
        initial_columns, initial_column_groups = report._build_columns_from_column_group_vals(
            initial_forced_options, initial_column_group_vals)

        # End balance
        end_date_to = options['date']['date_to']
        end_date_from = options['comparison']['periods'][-1]['date_from'] if options['comparison']['periods'] else \
        options['date']['date_from']
        end_forced_options = {
            'end_balance': True,
            'date': {
                'mode': 'range',
                'currency_table_period_key': None,
                'date_to': fields.Date.from_string(end_date_to).strftime(DEFAULT_SERVER_DATE_FORMAT),
                'date_from': fields.Date.from_string(end_date_from).strftime(DEFAULT_SERVER_DATE_FORMAT)
            }
        }
        end_header_element = [{'name': _("End Balance"), 'forced_options': end_forced_options}]
        col_headers_end = [
            end_header_element,
            *options['column_headers'][1:],
        ]
        end_column_group_vals = report._generate_columns_group_vals_recursively(col_headers_end, default_group_vals)
        end_columns, end_column_groups = report._build_columns_from_column_group_vals(
            end_forced_options, end_column_group_vals)

        # Update options
        options['column_headers'][0] = initial_header_element + options['column_headers'][0] + end_header_element
        options['column_groups'].update(initial_column_groups)
        options['column_groups'].update(end_column_groups)
        options['columns'] = initial_columns + options['columns'] + end_columns
        options['ignore_totals_below_sections'] = True  # So that GL does not compute them
        # remove Send button
        indx_2remove = None
        for indx, btn in enumerate(options['buttons']):
            if btn.get('action', '') == 'action_send_statements':
                indx_2remove = indx
                break
        if indx_2remove:
            options['buttons'].remove(options['buttons'][indx_2remove])

    def _get_custom_display_config(self):
        return {
            'templates': {
                'AccountReportFilters': 'vas_debt_report.AccountReportFiltersCustomizable',
            },
        }

    def _update_report_line_move_line(self, new_line, old_line):
        # Update more column if  column value if
        group_col_data = new_line['columns']
        for index, val in enumerate(old_line['columns']):
            if val:
                group_col_data[index] = val
        new_line['columns'] = group_col_data
        return new_line

    # ===================================== HANDE XLXS ==========================================
    # ===================================== HANDE XLXS ==========================================
    # ===================================== HANDE XLXS ==========================================
    # ===================================== HANDE XLXS ==========================================
    # ===================================== HANDE XLXS ==========================================

    def export_to_xlsx(self, options, response=None):
        if not options.get('selected_currency_id'):
            raise ValidationError(_('Please select currency before export.'))

        report_id = self.env.ref('vas_debt_report.account_debt_report_data')
        report_lines = report_id.get_report_information(options)['lines']
        report_lines_json = []
        for line in report_lines:
            line_json = self._get_row_json_data(line)
            report_lines_json.append(line_json)

        return self.action_export_to_xlsx(report_lines_json, options['date'], options.get('name_account_group', ''),
            *options['selected_currency_id'])

    def _get_row_json_data(self, data):

        result = {}
        row = data.get('columns')
        # partner_id = data.get('id').split('~')[-1]

        if data.get('partner_id'):
            # partner = self.env['res.partner'].search([('id', '=', partner_id)])
            # result['customer_code'] = partner.customer_code if partner.customer_code else ""
            result['customer_code'] = ""

        if result.get('invoice_date') not in [None, '']:
            result['invoice_date'] = result.get('invoice_date').strftime("%d-%m-%Y")
            result['date'] = result['invoice_date']
            del result['invoice_date']
        if result.get('name') not in [None, '']:
            result['line_name'] = result['name']
        else:
            result['line_name'] = data['name']

        index = 0
        for cell in row:
            # if cell.get('expression_label') and cell.get('expression_label') != 'account_code':
            result[cell.get('expression_label', 'None') + f"_{index}"] = cell.get('no_format', 0)
            index += 1

        return result

    def action_export_to_xlsx(self, report_lines, date_range, group_account_name, currency_name):
        for i in ['date_from', 'date_to']:
            date_range[i] = datetime.strptime(date_range.get(i, '1990-01-01'), "%Y-%m-%d")
        custom_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        template_file_path = f"{custom_path}/static/report_templates/debt_currency_template.xlsx"

        wb = load_workbook(template_file_path)
        ws = wb.active

        self.write_data_for_sheet(ws, report_lines, date_range, group_account_name, currency_name)
        # save and return file
        filename_url = (f"debt_"
                        f"from_{date_range.get('date_from').strftime('%d%m%Y')}_to_{date_range.get('date_to').strftime('%d%m%Y')}.xlsx")
        fp = io.BytesIO()
        wb.save(fp)
        return {
            'file_name': filename_url,
            'file_content': fp.getvalue(),
            'file_type': 'xlsx',
        }

    def css_cell_text(self, cell, text_center=False, bold=False, italic=False, font_name='Times New Roman', size=11,
            background_color=False):
        cell.font = Font(font_name, size=size)
        if text_center:
            cell.alignment = Alignment(horizontal='center', vertical='center')
        if bold:
            cell.font = Font(font_name, bold=True, size=size)
        if italic:
            cell.font = Font(font_name, italic=True, size=size)
        if background_color:
            cell.fill = PatternFill(start_color=background_color, fill_type="solid")
        cell.number_format = '#,##0.00;-#,##0.00'

    def write_data_for_sheet(self, sheet, report_lines, date_range, group_account_name, currency_name):
        company = self.env.company
        exclude_table_values = {
            'company_name': {
                'col': 2,  # col B1
                'row': 1,
                'value': f"{company.display_name}\nĐịa chỉ: {company.street or ''} {company.street2 or ''} {company.city or ''} {company.state_id.name or ''} {company.country_id.name or ''}"
            },
            'name': {
                'col': 2,  # col B2
                'row': 2,
                'value': "SỔ TỔNG HỢP CÔNG NỢ NGOẠI TỆ",
            },
            'date': {
                'col': 2,  # col B3
                'row': 3,
                'value': f"Từ ngày {date_range.get('date_from').strftime('%d-%m-%Y')} đến ngày {date_range.get('date_to').strftime('%d-%m-%Y')}",
            },
            'account': {
                'col': 2,  # col B4
                'row': 4,
                'value': f"Tài khoản: {group_account_name}                                  ĐVT: {currency_name}",
            }
        }

        for key, row in exclude_table_values.items():
            cell = sheet.cell(row=row['row'], column=row['col'])
            cell.value = row['value']
            merge_add = row.get('merge_add')
            if merge_add:
                sheet.merge_cells(start_row=row['row'],
                    start_column=row['col'], end_row=row['row'], end_column=row['col'] + merge_add)

        # write move line row
        table_row = 9  # start from row 9
        black_thin = Side(border_style="thin", color="000000")

        last_line = report_lines[-1]
        report_lines.pop(-1)

        for index, line in enumerate(report_lines):
            start_column = 2  # start at 2
            for key, value in line.items():
                cell = sheet.cell(row=table_row, column=start_column)

                if start_column == 2:
                    cell.alignment = Alignment(horizontal='left', vertical='center')

                cell.value = value
                self.css_cell_text(cell=cell)
                cell.border = Border(top=black_thin, left=black_thin, right=black_thin, bottom=black_thin)
                if start_column != 3:
                    cell.number_format = '#,##0.00;-#,##0.00'
                start_column += 1
            table_row += 1

        empty_column = {'empty': ''}
        index = list(last_line.keys()).index('line_name')
        last_line = dict(list(last_line.items())[:index] + list(empty_column.items()) + list(last_line.items())[index:])

        start_column = 2  # start at 2
        for key, value in last_line.items():
            cell = sheet.cell(row=8, column=start_column)
            cell.number_format = '#,##0.00;-#,##0.00'
            cell.border = Border(top=black_thin, left=black_thin, right=black_thin, bottom=black_thin)
            self.css_cell_text(cell, bold=True, background_color="fdf5e6")
            if start_column == 3:
                cell.value = "Khách hàng mua"
            else:
                cell.value = value

            cell_total = sheet.cell(row=table_row, column=start_column)
            cell.number_format = '#,##0.00;-#,##0.00'
            cell_total.border = Border(top=black_thin, left=black_thin, right=black_thin, bottom=black_thin)
            self.css_cell_text(cell_total, bold=True, background_color="fafad2")
            if start_column == 3:
                cell_total.value = "Tổng cộng"
            else:
                cell_total.value = value

            start_column += 1

        sign_row = table_row + 3
        sign_rows = [
            {
                'value': 'Kế toán ghi sổ',  # Ax-Bx
                'row': sign_row,
                'col': 1,
                'bold': True,
                'merge_add': 2
            },
            {
                'value': '(Ký, họ tên)',  # Ax+1-Bx+1
                'row': sign_row + 1,
                'col': 1,
                'merge_add': 2,
                'italic': True
            },
            {
                'value': 'Kế toán trưởng',  # Ex
                'row': sign_row,
                'col': 4,
                'bold': True,
            },
            {
                'value': '(Ký, họ tên)',  # Ex+1
                'row': sign_row + 1,
                'col': 4,
                'italic': True
            },
            {
                'value': 'Ngày ..... tháng ..... năm ..... ',  # Gx-Hx-Ix
                'row': sign_row - 1,
                'col': 5,
                'italic': True,
                'merge_add': 4,
            },
            {
                'value': 'Giám đốc',  # Gx-Hx-Ix
                'row': sign_row,
                'col': 5,
                'bold': True,
                'merge_add': 4,
            },
            {
                'value': 'Ký, họ tên, đóng dấu',  # Gx-Hx-Ix
                'row': sign_row + 1,
                'col': 5,
                'italic': True,
                'merge_add': 4,
            },
        ]

        # cell Cxx
        for sign in sign_rows:
            cell = sheet.cell(row=sign['row'], column=sign['col'])
            cell.font = Font(size=14)
            cell.value = sign['value']
            if not sign.get('skip_text_center'):
                self.css_cell_text(cell, text_center=True)
            if sign.get('bold'):
                self.css_cell_text(cell, bold=True)
            if sign.get('italic'):
                self.css_cell_text(cell, italic=True)

            merge_add = sign.get('merge_add')
            if merge_add:
                sheet.merge_cells(start_row=sign['row'],
                    start_column=sign['col'], end_row=sign['row'], end_column=sign['col'] + merge_add)

    def _get_sums_without_partner(self, options):
        """ Get the sum of lines without partner reconciled with a line with a partner, grouped by partner. Those lines
        should be considered as belonging to the partner for the reconciled amount as it may clear some of the partner
        invoice/bill and they have to be accounted in the partner balance."""
        queries = []
        report = self.env.ref('vas_debt_report.account_debt_report_data')
        domain_param = [
            # ('currency_id', '!=', self.env.company.currency_id.id),
            ('currency_id', '!=', False),
            ('account_id.follow_by_partner', '=', True)
        ]
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(column_group_options, 'strict_range', domain=domain_param)
            queries.append(SQL(
                """
                SELECT
                    %(column_group_key)s        AS column_group_key,
                    aml_with_partner.partner_id AS groupby,
                    SUM(%(debit_select)s)       AS debit,
                    SUM(%(credit_select)s)      AS credit,
                    SUM(%(balance_select)s)     AS amount,
                    SUM(%(balance_select)s)     AS balance
                FROM %(table_references)s
                JOIN account_partial_reconcile partial
                    ON account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id
                JOIN account_move_line aml_with_partner ON
                    (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                    AND aml_with_partner.partner_id IS NOT NULL
                %(currency_table_join)s
                WHERE partial.max_date <= %(date_to)s AND %(search_condition)s
                    AND account_move_line.partner_id IS NULL
                    AND account_move_line.debit !=0
                GROUP BY aml_with_partner.partner_id, aml_with_partner.currency_id
                UNION ALL
                SELECT
                    %(column_group_key)s        AS column_group_key,
                    aml_with_partner.partner_id AS groupby,
                    SUM(%(debit_select)s)       AS debit,
                    SUM(%(credit_select)s)      AS credit,
                    SUM(%(balance_select)s)     AS amount,
                    SUM(%(balance_select)s)     AS balance
                FROM %(table_references)s
                JOIN account_partial_reconcile partial
                    ON account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id
                JOIN account_move_line aml_with_partner ON
                    (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                    AND aml_with_partner.partner_id IS NOT NULL
                %(currency_table_join)s
                WHERE partial.max_date <= %(date_to)s AND %(search_condition)s
                    AND account_move_line.partner_id IS NULL
                    AND account_move_line.credit !=0
                GROUP BY aml_with_partner.partner_id, aml_with_partner.currency_id
                """,
                column_group_key=column_group_key,
                debit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE partial.amount END")),
                credit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE partial.amount END")),
                balance_select=report._currency_table_apply_rate(SQL("-SIGN(aml_with_partner.balance) * partial.amount")),
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(column_group_options, aml_alias=SQL("aml_with_partner")),
                date_to=column_group_options['date']['date_to'],
                search_condition=query.where_clause,
            ))

        return SQL(" UNION ALL ").join(queries)
