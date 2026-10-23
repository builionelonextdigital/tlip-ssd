# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.modules import get_module_resource


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _build_column_debt_currency_dict(
            self, col_value, col_data,
            options=None, currency=False, digits=1,
            column_expression=None, has_sublines=False,
            report_line_id=None,
    ):
        # Empty column
        if col_value is None and col_data is None:
            return {}

        col_data = col_data or {}
        column_expression = column_expression or self.env['account.report.expression']
        options = options or {}

        blank_if_zero = column_expression.blank_if_zero or col_data.get('blank_if_zero', False)
        figure_type = column_expression.figure_type or col_data.get('figure_type', 'string')

        if col_data.get('expression_label', '') not in ('debit_currency', 'credit_currency', 'amount_currency_debit', 'amount_currency_credit', 'amount_currency_balance') or not currency:
            currency = False
                
        format_params = {}
        if figure_type == 'monetary' and currency:
            format_params['currency_id'] = currency.id
        elif figure_type in ('float', 'percentage'):
            format_params['digits'] = digits

        return {
            'auditable': col_value is not None and column_expression.auditable,
            'blank_if_zero': blank_if_zero,
            'column_group_key': col_data.get('column_group_key'),
            'currency': currency.id if currency else None,
            'currency_symbol': currency.symbol if options.get('multi_currency') and currency else self.env.company.currency_id.symbol,
            'digits': digits,
            'expression_label': col_data.get('expression_label'),
            'figure_type': figure_type,
            'green_on_positive': column_expression.green_on_positive,
            'has_sublines': has_sublines,
            'is_zero': col_value is None or (
                isinstance(col_value, (int, float))
                and figure_type in ('float', 'integer', 'monetary')
                and self._is_value_zero(col_value, figure_type, format_params)
            ),
            'name': self._format_value(options, col_value, figure_type=figure_type, format_params=format_params),
            'no_format': col_value,
            'report_line_id': report_line_id,
            'sortable': col_data.get('sortable', False),
            'format_params': format_params,
        }