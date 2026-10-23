import logging
from collections import defaultdict

from odoo import models, api, _
from odoo.tools import get_lang

_logger = logging.getLogger(__name__)


class CipWipSummaryReportHandler(models.AbstractModel):
    _name = 'cip.wip.summary.report.handler'
    _inherit = 'account.report.custom.handler'
    _description = 'CIP/WIP Summary Report Custom Handler'

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        """Generate the report lines in flat table format"""
        lines = self._get_report_lines(report, options)
        return [(0, line) for line in lines]

    def _get_report_lines(self, report, options):
        """Main method to generate flat report lines"""

        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        company_ids = tuple(comp['id'] for comp in options.get(
            'multi_company') or [{'id': self.env.company.id}])

        # Query to get all detail lines with their balances
        query = """
            WITH move_lines_with_analytic AS (
                SELECT
                    aml.id as move_line_id,
                    aml.account_id,
                    aml.date,
                    aml.debit,
                    aml.credit,
                    aml.company_id,
                    aml.name as move_line_name,
                    aml.development_project_id,
                    aml.development_project_code,
                    aml.move_id,
                    CAST(jsonb_object_keys(aml.analytic_distribution) AS INTEGER) as analytic_account_id,
                    CAST(aml.analytic_distribution->>jsonb_object_keys(aml.analytic_distribution) AS FLOAT) / 100.0 as distribution_percentage
                FROM account_move_line aml
                    LEFT JOIN account_account acc ON acc.id = aml.account_id
                WHERE aml.parent_state = 'posted'
                    AND aml.analytic_distribution IS NOT NULL
                    AND aml.analytic_distribution != '{}'::jsonb
                    AND aml.development_project_id IS NOT NULL
                    AND aml.date <= %(date_to)s
                    AND aml.company_id IN %(company_ids)s
                    AND acc.use_for_cip = true
            ),
            balances AS (
                SELECT
                    ml.move_line_id,
                    ml.account_id,
                    ml.analytic_account_id,
                    ml.company_id,
                    ml.date,
                    ml.move_line_name,
                    ml.development_project_id,
                    ml.development_project_code as project_code,
                    ml.move_id,
                    dp.id as project_id,
                    dp.name as project_name,
                    aa.budget_code_id,
                    acc.code_store->>CAST(ml.company_id AS TEXT) as account_code,
                    acc.name->>CAST(ml.company_id AS TEXT) as account_name,
                    bc.code as budget_code,
                    bc.name as budget_name,

                    -- Calculate proportional amounts
                    CASE WHEN ml.date >= %(date_from)s AND ml.date <= %(date_to)s THEN SUM(ml.debit * ml.distribution_percentage) ELSE 0.0 END as period_debit,
                    CASE WHEN ml.date >= %(date_from)s AND ml.date <= %(date_to)s THEN SUM(ml.credit * ml.distribution_percentage) ELSE 0.0 END as period_credit
                FROM move_lines_with_analytic ml
                LEFT JOIN development_project dp ON dp.id = ml.development_project_id
                LEFT JOIN account_analytic_account aa ON aa.id = ml.analytic_account_id
                LEFT JOIN account_account acc ON acc.id = ml.account_id
                LEFT JOIN budget_code bc ON bc.id = aa.budget_code_id
                WHERE acc.use_for_cip = true and dp.active = true
                GROUP BY
                    ml.move_line_id,
                    ml.account_id,
                    ml.analytic_account_id,
                    ml.company_id,
                    ml.date,
                    ml.move_line_name,
                    ml.development_project_id,
                    ml.development_project_code,
                    ml.move_id,
                    dp.id,
                    dp.name,
                    aa.budget_code_id,
                    acc.code_store,
                    acc.name,
                    bc.code,
                    bc.name
            ),
            opening_balances AS (
                SELECT
                    b.account_id,
                    b.analytic_account_id,
                    b.development_project_id,
                    b.development_project_code,
                    COALESCE(SUM(b.period_debit), 0.0) as opening_debit,
                    COALESCE(SUM(b.period_credit), 0.0) as opening_credit
                FROM (
                    SELECT
                        ml.account_id,
                        ml.analytic_account_id,
                        ml.development_project_id,
                        ml.development_project_code,
                        ml.debit * ml.distribution_percentage as period_debit,
                        ml.credit * ml.distribution_percentage as period_credit
                    FROM (
                        SELECT
                            aml.account_id,
                            aml.debit,
                            aml.credit,
                            aml.development_project_id,
                            aml.development_project_code,
                            CAST(jsonb_object_keys(aml.analytic_distribution) AS INTEGER) as analytic_account_id,
                            CAST(aml.analytic_distribution->>jsonb_object_keys(aml.analytic_distribution) AS FLOAT) / 100.0 as distribution_percentage
                        FROM account_move_line aml
                            LEFT JOIN account_account acc ON acc.id = aml.account_id
                        WHERE aml.parent_state = 'posted'
                            AND aml.analytic_distribution IS NOT NULL
                            AND aml.analytic_distribution != '{}'::jsonb
                            AND aml.development_project_id IS NOT NULL
                            AND aml.date < %(date_from)s
                            AND aml.company_id IN %(company_ids)s
                            AND acc.use_for_cip = true
                    ) ml
                ) b
                GROUP BY b.account_id, b.analytic_account_id, b.development_project_id, b.development_project_code
            ),
            res AS ( 
                SELECT
                    b.project_id,
                    array_agg(b.move_line_id) as ml_ids,
                    b.project_code,
                    b.project_name,
                    b.budget_code,
                    b.budget_name,
                    SUM(b.period_debit) as period_debit,
                    SUM(b.period_credit) as period_credit
                FROM balances b
                GROUP BY
                    b.project_id,
                    b.project_code,
                    b.project_name,
                    b.budget_code_id,
                    b.budget_code,
                    b.budget_name
                ORDER BY b.budget_code)

            SELECT 
                *,
                COALESCE(ob.opening_debit, 0.0) + COALESCE(res.period_debit, 0.0) as ending_debit,
                COALESCE(ob.opening_credit, 0.0) + COALESCE(res.period_credit, 0.0) as ending_credit
            FROM res LEFT JOIN opening_balances ob ON ob.development_project_id = res.project_id AND ob.development_project_code = res.project_code
        """
        # TODO: check query analytic_account_id and budget_code_id are correct, may need to join on code instead of id depending on data structure
        params = {
            'date_from': date_from,
            'date_to': date_to,
            'company_ids': company_ids,
        }

        self.env.cr.execute(query, params)
        results = self.env.cr.dictfetchall()

        if not results:
            return []

        # Build flat lines
        return self._build_flat_lines(report, options, results)

    def _build_flat_lines(self, report, options, results):
        """Build report lines with project grouping and subtotals"""
        lang = self.env.context.get('lang') or get_lang(self.env).code
        lines = []

        # Add grouped header row (for "Opening Balance", "Occurred in this period", "Ending Balance")
        group_header_id = report._get_generic_line_id(
            None, None, markup='group_header_line')
        lines.append({
            'id': group_header_id,
            'name': '',
            'level': 0,
            'unfoldable': False,
            'unfolded': False,
            'class': 'cip_wip_group_header',
            'columns': [
                {'name': '', 'class': ''},
                {'name': '', 'class': ''},
                {'name': 'Opening Balance', 'class': 'text-center', 'colspan': 2},
                {'name': '', 'class': ''},
                {'name': 'Occurred in this period',
                    'class': 'text-center', 'colspan': 2},
                {'name': '', 'class': ''},
                {'name': 'Ending Balance', 'class': 'text-center', 'colspan': 2},
                {'name': '', 'class': ''},
            ],
        })

        # Add column header row (for "Debit", "Credit", etc.)
        header_line_id = report._get_generic_line_id(
            None, None, markup='header_line')
        lines.append({
            'id': header_line_id,
            'name': '',
            'level': 0,
            'unfoldable': False,
            'unfolded': False,
            'class': 'cip_wip_column_header',
            'columns': [
                {'name': 'Project Code', 'class': ''},
                {'name': 'Budget Code', 'class': ''},
                {'name': 'Debit', 'class': 'text-center'},
                {'name': 'Credit', 'class': 'text-center'},
                {'name': 'Increase', 'class': 'text-center'},
                {'name': 'Decrease', 'class': 'text-center'},
                {'name': 'Debit', 'class': 'text-center'},
                {'name': 'Credit', 'class': 'text-center'},
            ],
        })

        # Group results by project
        projects = defaultdict(list)
        for row in results:
            project_key = (row['project_id'],
                           row['project_code'], row['project_name'])
            projects[project_key].append(row)

        line_number = 0
        # Initialize grand totals
        grand_totals = {
            'opening_debit': 0.0,
            'opening_credit': 0.0,
            'period_debit': 0.0,
            'period_credit': 0.0,
            'ending_debit': 0.0,
            'ending_credit': 0.0,
        }

        # Process each project
        # Sort by project_code, handle None
        for project_key in sorted(projects.keys(), key=lambda x: x[1] or ''):
            # if not project_key[1]:
            #     continue  # Skip projects without a code
            project_id, project_code, project_name = project_key
            project_rows = projects[project_key]

            # Calculate project subtotals
            project_totals = {
                'opening_debit': 0.0,
                'opening_credit': 0.0,
                'period_debit': 0.0,
                'period_credit': 0.0,
                'ending_debit': 0.0,
                'ending_credit': 0.0,
            }

            for row in project_rows:
                project_totals['opening_debit'] += row['opening_debit'] or 0.0
                project_totals['opening_credit'] += row['opening_credit'] or 0.0
                project_totals['period_debit'] += row['period_debit']
                project_totals['period_credit'] += row['period_credit']
                project_totals['ending_debit'] += row['ending_debit']
                project_totals['ending_credit'] += row['ending_credit']

            # Add detail lines for each budget code first
            for row in project_rows:
                # Handle translated fields
                budget_name = self._get_translated_value(
                    row['budget_name'], lang)

                # Create unique line ID
                line_number += 1
                line_id = report._get_generic_line_id(
                    None, None,
                    markup=f'line_{row["project_id"]}_{row["budget_code"]}_{line_number}_{str(row["ml_ids"])}'
                )

                # Build display names
                budget_display = f'{row["budget_code"]} - {budget_name}' if budget_name and row["budget_code"] else (
                    row["budget_code"] or '')

                action_id = self.env.ref(
                    'tlip_account.action_cip_wip_summary_view_detail').id
                opening_balance = (row['opening_debit']
                                   or 0.0) - (row['opening_credit'] or 0.0)
                ending_balance = (row['ending_debit'] or 0.0) - \
                    (row['ending_credit'] or 0.0)
                lines.append({
                    'id': line_id,
                    'name': f'View Journal Items',
                    'level': 1,  # Level 1 for budget detail rows (no parent)
                    'unfoldable': False,
                    # 'action': 'action_view_journal_items',
                    'action_id': action_id,
                    # 'action_context': action_params,
                    'columns': [
                        # Project Code
                        {'name': project_code if project_code else 'No Code',
                            'no_format': project_code if project_code else 'No Code', 'class': ''},
                        # Budget Code
                        {'name': budget_display,
                            'no_format': budget_display, 'class': ''},
                        # Opening Balance - Debit
                        {'name': report.format_value(options, opening_balance >= 0 and opening_balance or 0.0, figure_type='monetary'),
                         'no_format': opening_balance >= 0 and opening_balance or 0.0, 'class': 'number'},
                        # Opening Balance - Credit
                        {'name': report.format_value(options, opening_balance < 0 and abs(
                            opening_balance) or 0.0, figure_type='monetary'), 'no_format': opening_balance < 0 and abs(opening_balance) or 0.0, 'class': 'number'},
                        # Occurred in this period - Increase (Debit)
                        {'name': report.format_value(
                            options, row['period_debit'], figure_type='monetary'), 'no_format': row['period_debit'], 'class': 'number'},
                        # Occurred in this period - Decrease (Credit)
                        {'name': report.format_value(
                            options, row['period_credit'], figure_type='monetary'), 'no_format': row['period_credit'], 'class': 'number'},
                        # Ending Balance - Debit
                        {'name': report.format_value(options, ending_balance >= 0 and ending_balance or 0.0, figure_type='monetary'),
                         'no_format': ending_balance >= 0 and ending_balance or 0.0, 'class': 'number'},
                        # Ending Balance - Credit
                        {'name': report.format_value(options, ending_balance < 0 and abs(
                            ending_balance) or 0.0, figure_type='monetary'), 'no_format': ending_balance < 0 and abs(ending_balance) or 0.0, 'class': 'number'},
                    ],
                })

            # Add project subtotal line at the bottom of the group
            project_line_id = report._get_generic_line_id(
                None, None, markup=f'project_subtotal_{project_id}')
            opening_total_balance = project_totals['opening_debit'] - \
                project_totals['opening_credit']
            ending_total_balance = project_totals['ending_debit'] - \
                project_totals['ending_credit']
            lines.append({
                'id': project_line_id + (project_code if project_code else 'No Code'),
                'name': '',
                'level': 1,
                'unfoldable': False,
                'class': 'cip_wip_project_subtotal',
                'columns': [
                    # Project Code
                    {'name': f'Total {project_code if project_code else "No Code"}',
                        'no_format': f'Total {project_code if project_code else "No Code"}', 'class': 'font-weight-bold'},
                    # Project Name
                    {'name': '', 'class': ''},
                    # Budget Code (empty for subtotal)
                    {'name': '', 'class': ''},
                    # Opening Balance - Debit
                    {'name': report.format_value(options, opening_total_balance >= 0 and opening_total_balance or 0.0, figure_type='monetary'),
                     'no_format': opening_total_balance >= 0 and opening_total_balance or 0.0, 'class': 'number font-weight-bold'},
                    # Opening Balance - Credit
                    {'name': report.format_value(options, opening_total_balance < 0 and abs(opening_total_balance) or 0.0, figure_type='monetary'),
                     'no_format': opening_total_balance < 0 and abs(opening_total_balance) or 0.0, 'class': 'number font-weight-bold'},
                    # Occurred in this period - Increase (Debit)
                    {'name': report.format_value(options, project_totals['period_debit'], figure_type='monetary'),
                     'no_format': project_totals['period_debit'], 'class': 'number font-weight-bold'},
                    # Occurred in this period - Decrease (Credit)
                    {'name': report.format_value(options, project_totals['period_credit'], figure_type='monetary'),
                     'no_format': project_totals['period_credit'], 'class': 'number font-weight-bold'},
                    # Ending Balance - Debit
                    {'name': report.format_value(options, ending_total_balance >= 0 and ending_total_balance or 0.0, figure_type='monetary'),
                     'no_format': ending_total_balance >= 0 and ending_total_balance or 0.0, 'class': 'number font-weight-bold'},
                    # Ending Balance - Credit
                    {'name': report.format_value(options, ending_total_balance < 0 and abs(ending_total_balance) or 0.0, figure_type='monetary'),
                     'no_format': ending_total_balance < 0 and abs(ending_total_balance) or 0.0, 'class': 'number font-weight-bold'},
                ],
            })

            # Accumulate to grand totals
            grand_totals['opening_debit'] += project_totals['opening_debit']
            grand_totals['opening_credit'] += project_totals['opening_credit']
            grand_totals['period_debit'] += project_totals['period_debit']
            grand_totals['period_credit'] += project_totals['period_credit']
            grand_totals['ending_debit'] += project_totals['ending_debit']
            grand_totals['ending_credit'] += project_totals['ending_credit']

        # Add grand totals row
        totals_line_id = report._get_generic_line_id(
            None, None, markup='totals_line')
        opening_grand_total_balance = grand_totals['opening_debit'] - \
            grand_totals['opening_credit']
        ending_grand_total_balance = grand_totals['ending_debit'] - \
            grand_totals['ending_credit']
        lines.append({
            'id': totals_line_id,
            'name': '',
            'level': 0,
            'unfoldable': False,
            'unfolded': False,
            'class': 'cip_wip_totals',
            'columns': [
                {'name': 'Grand Total', 'class': 'text-center font-weight-bold'},
                {'name': '', 'class': ''},
                # Opening Balance - Debit
                {'name': report.format_value(
                    options, opening_grand_total_balance >= 0 and opening_grand_total_balance or 0.0, figure_type='monetary'), 'no_format': opening_grand_total_balance >= 0
                 and opening_grand_total_balance or 0.0, 'class': 'number'},
                # Opening Balance - Credit
                {'name': report.format_value(
                    options, opening_grand_total_balance < 0 and abs(opening_grand_total_balance) or 0.0, figure_type='monetary'), 'no_format': opening_grand_total_balance < 0
                 and abs(opening_grand_total_balance) or 0.0, 'class': 'number'},
                # Occurred in this period - Increase (Debit)
                {'name': report.format_value(
                    options, grand_totals['period_debit'], figure_type='monetary'), 'no_format': grand_totals['period_debit'], 'class': 'number'},
                # Occurred in this period - Decrease (Credit)
                {'name': report.format_value(
                    options, grand_totals['period_credit'], figure_type='monetary'), 'no_format': grand_totals['period_credit'], 'class': 'number'},
                # Ending Balance - Debit
                {'name': report.format_value(
                    options, ending_grand_total_balance >= 0 and ending_grand_total_balance or 0.0, figure_type='monetary'), 'no_format': ending_grand_total_balance >= 0
                 and ending_grand_total_balance or 0.0, 'class': 'number'},
                # Ending Balance - Credit
                {'name': report.format_value(
                    options, ending_grand_total_balance < 0 and abs(ending_grand_total_balance) or 0.0, figure_type='monetary'), 'no_format': ending_grand_total_balance < 0
                 and abs(ending_grand_total_balance) or 0.0, 'class': 'number'},
            ],
        })

        return lines

    def _get_translated_value(self, value, lang):
        """Extract translated value from dict or return string as-is"""
        if isinstance(value, dict):
            return value.get(lang) or list(value.values())[0] if value else ''
        return value or ''
