# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import SQL, Query
from odoo.tools.misc import get_lang


class CashFlowReportCustomHandler(models.AbstractModel):
    _inherit = 'account.cash.flow.report.handler'

    def _dispatch_aml_data(self, tags_ids, aml_data, layout_data, report_data):
        if aml_data and aml_data.get("account_id"):
            if self.env["account.account"].browse(int(aml_data.get("account_id"))).account_type in ["asset_current", "expense_direct_cost"]:
                return
        return super(CashFlowReportCustomHandler, self)._dispatch_aml_data(tags_ids, aml_data, layout_data, report_data)
 
    def _get_move_ids_query(self, report, payment_account_ids, options):
        if report and report.custom_handler_model_name == "account.cash.flow.report.handler":
            filtered_accounts = self.env["account.account"].browse(payment_account_ids).filtered(
                lambda x: x.account_type not in ["asset_current", "expense_direct_cost"]
            )
            payment_account_ids = tuple(filtered_accounts.ids)
        
        return super()._get_move_ids_query(report, payment_account_ids, options)
    
    def _get_report_data(self, report, options, layout_data):
        """Get the report data with support for analytic account grouping.
        
        :param report: The report object
        :param options: The report options
        :param layout_data: The layout data for the report
        :return: The processed report data
        """
        report_data = super()._get_report_data(report, options, layout_data)

        payment_account_ids = self._get_account_ids(report, options)
        if not payment_account_ids:
            return report_data

        tags_ids = self._get_tags_ids()
        cashflow_tag_ids = self._get_cashflow_tag_ids()

        # Process analytic grouping if enabled
        if options.get("analytic_accounts_groupby"):
            for account_group_by in options.get("analytic_accounts_groupby"):
                # Process liquidity moves with analytic grouping
                for aml_groupby_account in self._custom_get_liquidity_moves(
                    report, 
                    options,
                    payment_account_ids,
                    cashflow_tag_ids,
                    account_group_by
                ):
                    for aml_data in aml_groupby_account.values():
                        self._dispatch_aml_data(tags_ids, aml_data, layout_data, report_data)

                # Process reconciled moves with analytic grouping
                for aml_groupby_account in self._custom_get_reconciled_moves(
                    report,
                    options,
                    payment_account_ids,
                    cashflow_tag_ids,
                    account_group_by
                ):
                    for aml_data in aml_groupby_account.values():
                        self._dispatch_aml_data(tags_ids, aml_data, layout_data, report_data)

        return report_data
    
    def _get_custom_move_ids_query(self, report, payment_account_ids, column_group_options, account_group_by=None) -> SQL:
        ''' Get all liquidity moves to be part of the cash flow statement with analytic distribution support.
        
        :param report: The report object
        :param payment_account_ids: A tuple containing all account.account's ids being used in a liquidity journal
        :param column_group_options: The options for the current column group
        :param account_group_by: The analytic account ID to group by
        :return: SQL query to retrieve the move IDs
        '''
        # Get the base query from the report
        query = report._get_report_query(
            column_group_options,
            'strict_range',
            [('account_id', 'in', list(payment_account_ids))]
        )

        # If we have an analytic account to group by, add the condition
        if account_group_by:
            query.add_where(SQL(
                'account_move_line.analytic_distribution::jsonb ? %(analytic_account)s',
                analytic_account=str(account_group_by)
            ))

        return SQL(
            '''
            SELECT
                array_agg(DISTINCT account_move_line.move_id) AS move_id
            FROM %(table_references)s
            WHERE %(search_condition)s
            ''',
            table_references=query.from_clause,
            search_condition=query.where_clause,
        )
    
    def _custom_get_liquidity_moves(self, report, options, payment_account_ids, cash_flow_tag_ids, account_group_by):
        ''' Fetch all information needed to compute lines from liquidity moves with analytic distribution.
        The difficulty is to represent only the not-reconciled part of balance.

        :param report:               The report object.
        :param options:             The report options.
        :param payment_account_ids: A tuple containing all account.account's ids being used in a liquidity journal.
        :param cash_flow_tag_ids:   A tuple containing the account.account.tag ids used in cash flow statements.
        :param account_group_by:    The analytic account ID to group by.
        :return:                    A list of tuple (account_id, account_code, account_name, account_type, amount).
        '''
        reconciled_aml_groupby_account = {}

        # Find the specific column group for analytic account
        custom_column_group_key = False
        for group_key in options['column_groups']:
            group_options = report._get_column_group_options(options, group_key)
            if group_options.get("analytic_accounts_list") and group_options.get("analytic_accounts_list")[0] == account_group_by:
                custom_column_group_key = group_key
                break

        queries = []

        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            if column_group_options and not 'analytic_accounts_list' in column_group_options:
                continue
            if column_group_key != custom_column_group_key:
                continue

            move_ids_query = self._get_custom_move_ids_query(report, payment_account_ids, column_group_options, account_group_by)
            query = Query(self.env, 'account_move_line')
            account_alias = query.join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
            account_type = SQL.identifier(account_alias, 'account_type')

            analytic_balance = SQL(
                "CAST(account_move_line.analytic_distribution::json->>%(account_group_by)s AS DECIMAL) / 100",
                account_group_by=account_group_by
            )

            queries.append(SQL(
                '''
                (WITH payment_move_ids AS (%(move_ids_query)s)
                -- Credit amount of each account
                SELECT
                    %(column_group_key)s AS column_group_key,
                    account_move_line.account_id,
                    %(account_code)s AS account_code,
                    %(account_name)s AS account_name,
                    %(account_type)s AS account_account_type,
                    account_account_account_tag.account_account_tag_id AS account_tag_id,
                    SUM(%(partial_amount_select)s * %(analytic_balance)s) AS balance
                FROM %(from_clause)s
                %(currency_table_join)s
                LEFT JOIN account_partial_reconcile
                    ON account_partial_reconcile.credit_move_id = account_move_line.id
                LEFT JOIN account_account_account_tag
                    ON account_account_account_tag.account_account_id = account_move_line.account_id
                    AND account_account_account_tag.account_account_tag_id IN %(cash_flow_tag_ids)s
                WHERE account_move_line.move_id IN (SELECT unnest(payment_move_ids.move_id) FROM payment_move_ids)
                    AND account_move_line.account_id NOT IN %(payment_account_ids)s
                    AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    AND account_move_line.analytic_distribution::json ? %(account_group_by)s
                GROUP BY account_move_line.company_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id

                UNION ALL

                -- Debit amount of each account
                SELECT
                    %(column_group_key)s AS column_group_key,
                    account_move_line.account_id,
                    %(account_code)s AS account_code,
                    %(account_name)s AS account_name,
                    %(account_type)s AS account_account_type,
                    account_account_account_tag.account_account_tag_id AS account_tag_id,
                    -SUM(%(partial_amount_select)s * %(analytic_balance)s) AS balance
                FROM %(from_clause)s
                %(currency_table_join)s
                LEFT JOIN account_partial_reconcile
                    ON account_partial_reconcile.debit_move_id = account_move_line.id
                LEFT JOIN account_account_account_tag
                    ON account_account_account_tag.account_account_id = account_move_line.account_id
                    AND account_account_account_tag.account_account_tag_id IN %(cash_flow_tag_ids)s
                WHERE account_move_line.move_id IN (SELECT unnest(payment_move_ids.move_id) FROM payment_move_ids)
                    AND account_move_line.account_id NOT IN %(payment_account_ids)s
                    AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    AND account_move_line.analytic_distribution::json ? %(account_group_by)s
                GROUP BY account_move_line.company_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id

                UNION ALL

                -- Total amount of each account
                SELECT
                    %(column_group_key)s AS column_group_key,
                    account_move_line.account_id AS account_id,
                    %(account_code)s AS account_code,
                    %(account_name)s AS account_name,
                    %(account_type)s AS account_account_type,
                    account_account_account_tag.account_account_tag_id AS account_tag_id,
                    SUM(%(aml_balance_select)s * %(analytic_balance)s) AS balance
                FROM %(from_clause)s
                %(currency_table_join)s
                LEFT JOIN account_account_account_tag
                    ON account_account_account_tag.account_account_id = account_move_line.account_id
                    AND account_account_account_tag.account_account_tag_id IN %(cash_flow_tag_ids)s
                WHERE account_move_line.move_id IN (SELECT unnest(payment_move_ids.move_id) FROM payment_move_ids)
                    AND account_move_line.account_id NOT IN %(payment_account_ids)s
                    AND account_move_line.analytic_distribution::json ? %(account_group_by)s
                GROUP BY account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id)
                ''',
                column_group_key=column_group_key,
                move_ids_query=move_ids_query,
                account_code=account_code,
                account_name=account_name,
                account_type=account_type,
                from_clause=query.from_clause,
                currency_table_join=report._currency_table_aml_join(options),
                partial_amount_select=report._currency_table_apply_rate(SQL("account_partial_reconcile.amount")),
                aml_balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                cash_flow_tag_ids=tuple(cash_flow_tag_ids),
                payment_account_ids=payment_account_ids,
                date_from=column_group_options['date']['date_from'],
                date_to=column_group_options['date']['date_to'],
                account_group_by=account_group_by,
                analytic_balance=analytic_balance,
            ))

        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            reconciled_aml_groupby_account.setdefault(aml_data['account_id'], {})
            reconciled_aml_groupby_account[aml_data['account_id']].setdefault(aml_data['column_group_key'], {
                'column_group_key': aml_data['column_group_key'],
                'account_id': aml_data['account_id'],
                'account_code': aml_data['account_code'],
                'account_name': aml_data['account_name'],
                'account_account_type': aml_data['account_account_type'],
                'account_tag_id': aml_data['account_tag_id'],
                'balance': 0.0,
            })
            
            if aml_data['balance'] is not None:
                reconciled_aml_groupby_account[aml_data['account_id']][aml_data['column_group_key']]['balance'] -= aml_data['balance']

        return list(reconciled_aml_groupby_account.values())

    def _custom_get_reconciled_moves(self, report, options, payment_account_ids, cash_flow_tag_ids, account_group_by):
        ''' Retrieve all moves being not a liquidity move to be shown in the cash flow statement.
        Each amount must be valued at the percentage of what is actually paid and considers analytic distribution.
        '''
        reconciled_account_ids = {column_group_key: set() for column_group_key in options['column_groups']}
        reconciled_percentage_per_move = {column_group_key: {} for column_group_key in options['column_groups']}
        currency_table = report._get_currency_table(options)

        # Find the specific column group for analytic account
        custom_column_group_key = False
        for group_key in options['column_groups']:
            group_options = report._get_column_group_options(options, group_key)
            if group_options.get("analytic_accounts_list") and group_options.get("analytic_accounts_list")[0] == account_group_by:
                custom_column_group_key = group_key
                break

        queries = []

        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            if column_group_options and not 'analytic_accounts_list' in column_group_options:
                continue
            if column_group_key != custom_column_group_key:
                continue

            move_ids_query = self._get_custom_move_ids_query(report, payment_account_ids, column_group_options, account_group_by)

            queries.append(SQL(
                '''
                (WITH payment_move_ids AS (%(move_ids_query)s)
                SELECT
                    %(column_group_key)s AS column_group_key,
                    debit_line.move_id,
                    debit_line.account_id,
                    SUM(%(partial_amount)s * CAST(credit_line.analytic_distribution::json->>%(account_group_by)s AS DECIMAL) / 100) AS balance
                FROM account_move_line AS credit_line
                LEFT JOIN account_partial_reconcile
                    ON account_partial_reconcile.credit_move_id = credit_line.id
                JOIN %(currency_table)s
                    ON account_currency_table.company_id = account_partial_reconcile.company_id
                    AND account_currency_table.rate_type = 'current'
                INNER JOIN account_move_line AS debit_line
                    ON debit_line.id = account_partial_reconcile.debit_move_id
                WHERE credit_line.move_id IN (SELECT unnest(payment_move_ids.move_id) FROM payment_move_ids)
                    AND credit_line.account_id NOT IN %(payment_account_ids)s
                    AND credit_line.credit > 0.0
                    AND debit_line.move_id NOT IN (SELECT unnest(payment_move_ids.move_id) FROM payment_move_ids)
                    AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                GROUP BY debit_line.move_id, debit_line.account_id

                UNION ALL

                SELECT
                    %(column_group_key)s AS column_group_key,
                    credit_line.move_id,
                    credit_line.account_id,
                    -SUM(%(partial_amount)s * CAST(debit_line.analytic_distribution::json->>%(account_group_by)s AS DECIMAL) / 100) AS balance
                FROM account_move_line AS debit_line
                LEFT JOIN account_partial_reconcile
                    ON account_partial_reconcile.debit_move_id = debit_line.id
                JOIN %(currency_table)s
                    ON account_currency_table.company_id = account_partial_reconcile.company_id
                    AND account_currency_table.rate_type = 'current'
                INNER JOIN account_move_line AS credit_line
                    ON credit_line.id = account_partial_reconcile.credit_move_id
                WHERE debit_line.move_id IN (SELECT unnest(payment_move_ids.move_id) FROM payment_move_ids)
                    AND debit_line.account_id NOT IN %(payment_account_ids)s
                    AND debit_line.debit > 0.0
                    AND credit_line.move_id NOT IN (SELECT unnest(payment_move_ids.move_id) FROM payment_move_ids)
                    AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                GROUP BY credit_line.move_id, credit_line.account_id)
                ''',
                move_ids_query=move_ids_query,
                column_group_key=column_group_key,
                payment_account_ids=payment_account_ids,
                date_from=column_group_options['date']['date_from'],
                date_to=column_group_options['date']['date_to'],
                currency_table=currency_table,
                partial_amount=report._currency_table_apply_rate(SQL("account_partial_reconcile.amount")),
                account_group_by=account_group_by,
            ))

        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            reconciled_percentage_per_move[aml_data['column_group_key']].setdefault(aml_data['move_id'], {})
            reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']].setdefault(aml_data['account_id'], [0.0, 0.0])
            if aml_data["balance"] is None:
                aml_data["balance"] = 0.0
            reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']][aml_data['account_id']][0] += aml_data['balance']
            reconciled_account_ids[aml_data['column_group_key']].add(aml_data['account_id'])

        if not reconciled_percentage_per_move:
            return []

        queries = []

        for column in options['columns']:
            if column and column.get("column_group_key") != custom_column_group_key:
                continue
                
            queries.append(SQL(
                '''
                SELECT
                    %(column_group_key)s AS column_group_key,
                    account_move_line.move_id,
                    account_move_line.account_id,
                    SUM(%(balance_select)s) AS balance
                FROM account_move_line
                JOIN %(currency_table)s
                    ON account_currency_table.company_id = account_move_line.company_id
                    AND account_currency_table.rate_type = 'current'
                WHERE account_move_line.move_id IN %(move_ids)s
                    AND account_move_line.account_id IN %(account_ids)s
                    AND account_move_line.analytic_distribution::json ? %(account_group_by)s
                GROUP BY account_move_line.move_id, account_move_line.account_id
                ''',
                column_group_key=column['column_group_key'],
                currency_table=currency_table,
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                move_ids=tuple(reconciled_percentage_per_move[column['column_group_key']].keys()) or (None,),
                account_ids=tuple(reconciled_account_ids[column['column_group_key']]) or (None,),
                account_group_by=account_group_by,
            ))

        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            if aml_data['account_id'] in reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']]:
                reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']][aml_data['account_id']][1] += aml_data['balance']

        reconciled_aml_per_account = {}

        queries = []

        query = Query(self.env, 'account_move_line')
        account_alias = query.join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
        account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
        account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
        account_type = SQL.identifier(account_alias, 'account_type')

        for column in options['columns']:
            if column and column.get("column_group_key") != custom_column_group_key:
                continue

            queries.append(SQL(
                '''
                SELECT
                    %(column_group_key)s AS column_group_key,
                    account_move_line.move_id,
                    account_move_line.account_id,
                    %(account_code)s AS account_code,
                    %(account_name)s AS account_name,
                    %(account_type)s AS account_account_type,
                    account_account_account_tag.account_account_tag_id AS account_tag_id,
                    SUM(%(balance_select)s * CAST(account_move_line.analytic_distribution::json->>%(account_group_by)s AS DECIMAL) / 100) AS balance
                FROM %(from_clause)s
                %(currency_table_join)s
                LEFT JOIN account_account_account_tag
                    ON account_account_account_tag.account_account_id = account_move_line.account_id
                    AND account_account_account_tag.account_account_tag_id IN %(cash_flow_tag_ids)s
                WHERE account_move_line.move_id IN %(move_ids)s
                    AND account_move_line.analytic_distribution::json ? %(account_group_by)s
                GROUP BY account_move_line.move_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id
                ''',
                column_group_key=column['column_group_key'],
                account_code=account_code,
                account_name=account_name,
                account_type=account_type,
                from_clause=query.from_clause,
                currency_table_join=report._currency_table_aml_join(options),
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                cash_flow_tag_ids=tuple(cash_flow_tag_ids),
                move_ids=tuple(reconciled_percentage_per_move[column['column_group_key']].keys()) or (None,),
                account_group_by=account_group_by,
            ))

        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            aml_column_group_key = aml_data['column_group_key']
            aml_move_id = aml_data['move_id']
            aml_account_id = aml_data['account_id']
            aml_account_code = aml_data['account_code']
            aml_account_name = aml_data['account_name']
            aml_account_account_type = aml_data['account_account_type']
            aml_account_tag_id = aml_data['account_tag_id']
            aml_balance = aml_data['balance']

            reconciled_aml_per_account.setdefault(aml_account_id, {})
            reconciled_aml_per_account[aml_account_id].setdefault(aml_column_group_key, {
                'column_group_key': aml_column_group_key,
                'account_id': aml_account_id,
                'account_code': aml_account_code,
                'account_name': aml_account_name,
                'account_account_type': aml_account_account_type,
                'account_tag_id': aml_account_tag_id,
                'balance': 0.0,
            })
            reconciled_aml_per_account[aml_account_id][aml_column_group_key]['balance'] -= aml_balance

        return list(reconciled_aml_per_account.values())