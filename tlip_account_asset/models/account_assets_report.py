
from odoo import fields, models, _
from odoo.tools import format_date, SQL, Query
from collections import defaultdict

MAX_NAME_LENGTH = 50


class AssetsReportCustomHandler(models.AbstractModel):
    _inherit = 'account.asset.report.handler'

    def _query_values(self, options, prefix_to_match=None, forced_account_id=None):
        "Override this function to filter based on asset type for fixasset"

        self.env['account.move.line'].check_access('read')
        self.env['account.asset'].check_access('read')

        query = Query(self.env, alias='asset', table=SQL.identifier('account_asset'))
        account_alias = query.join(lhs_alias='asset', lhs_column='account_asset_id', rhs_table='account_account', rhs_column='id', link='account_asset_id')
        query.add_join('LEFT JOIN', alias='move', table='account_move', condition=SQL(f"""
            move.asset_id = asset.id AND move.state {"!= 'cancel'" if options.get('all_entries') else "= 'posted'"}
        """))

        account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
        account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
        account_id = SQL.identifier(account_alias, 'id')

        if prefix_to_match:
            query.add_where(SQL("asset.name ILIKE %s", f"{prefix_to_match}%"))
        if forced_account_id:
            query.add_where(SQL("%s = %s", account_id, forced_account_id))

        analytic_account_ids = []
        if options.get('analytic_accounts') and not any(x in options.get('analytic_accounts_list', []) for x in options['analytic_accounts']):
            analytic_account_ids += [[str(account_id) for account_id in options['analytic_accounts']]]
        if options.get('analytic_accounts_list'):
            analytic_account_ids += [[str(account_id) for account_id in options.get('analytic_accounts_list')]]
        if analytic_account_ids:
            query.add_where(SQL('%s && %s', analytic_account_ids, self.env['account.asset']._query_analytic_accounts('asset')))

        selected_journals = tuple(journal['id'] for journal in options.get('journals', []) if journal['model'] == 'account.journal' and journal['selected'])
        if selected_journals:
            query.add_where(SQL("asset.journal_id in %s", selected_journals))

        sql = SQL(
            """
            SELECT asset.id AS asset_id,
                   asset.parent_id AS parent_id,
                   asset.name AS asset_name,
                   asset.asset_group_id AS asset_group_id,
                   asset.original_value AS asset_original_value,
                   asset.currency_id AS asset_currency_id,
                   COALESCE(asset.salvage_value, 0) as asset_salvage_value,
                   MIN(move.date) AS asset_date,
                   asset.disposal_date AS asset_disposal_date,
                   asset.acquisition_date AS asset_acquisition_date,
                   asset.method AS asset_method,
                   asset.method_number AS asset_method_number,
                   asset.method_period AS asset_method_period,
                   asset.method_progress_factor AS asset_method_progress_factor,
                   asset.state AS asset_state,
                   asset.company_id AS company_id,
                   %(account_code)s AS account_code,
                   %(account_name)s AS account_name,
                   %(account_id)s AS account_id,
                   COALESCE(SUM(move.depreciation_value) FILTER (WHERE move.date < %(date_from)s), 0) + COALESCE(asset.already_depreciated_amount_import, 0) AS depreciated_before,
                   COALESCE(SUM(move.depreciation_value) FILTER (WHERE move.date BETWEEN %(date_from)s AND %(date_to)s), 0) AS depreciated_during,
                   COALESCE(SUM(move.depreciation_value) FILTER (WHERE move.date BETWEEN %(date_from)s AND %(date_to)s AND move.asset_number_days IS NULL), 0) AS asset_disposal_value
              FROM %(from_clause)s
             WHERE %(where_clause)s
               AND asset.asset_type = 'fixed_asset'
               AND asset.company_id in %(company_ids)s
               AND (asset.acquisition_date <= %(date_to)s OR move.date <= %(date_to)s)
               AND (asset.disposal_date >= %(date_from)s OR asset.disposal_date IS NULL)
               AND (asset.state not in ('model', 'draft', 'cancelled') OR (asset.state = 'draft' AND %(include_draft)s))
               AND asset.active = 't'
          GROUP BY asset.id, account_id, account_code, account_name
          ORDER BY account_code, asset.acquisition_date, asset.id;
            """,
            account_code=account_code,
            account_name=account_name,
            account_id=account_id,
            date_from=options['date']['date_from'],
            date_to=options['date']['date_to'],
            from_clause=query.from_clause,
            where_clause=query.where_clause or SQL('TRUE'),
            company_ids=tuple(self.env['account.report'].get_report_company_ids(options)),
            include_draft=options.get('all_entries', False),
        )

        self._cr.execute(sql)
        results = self._cr.dictfetchall()
        return results
