from odoo import api, fields, models, Command, _
from odoo.tools.date_utils import end_of, start_of
from odoo.tools import (
    float_compare,
    formatLang,
    get_lang,
    float_round
)
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _must_check_constrains_date_sequence(self):
        if self.env.context.get('skip_date_sequence_check'):
            return False
        return super()._must_check_constrains_date_sequence()

    linked_asset_type = fields.Char(compute="_compute_asset_ids")
    asset_ids = fields.Many2many(
        'account.asset', string='Assets', compute="_compute_asset_ids")
    revaluation_reason_id = fields.Many2one('asset.revaluation.reason')

    # Overwrite to add logic for revenue and expense
    @api.depends('line_ids.balance')
    def _compute_depreciation_value(self):
        for move in self:
            # reversed moves are created before being assigned to the asset
            asset = move.asset_id or move.reversed_entry_id.asset_id
            if asset:
                account_internal_group = 'income' if asset.asset_type == 'sale' else 'expense'
                asset_expense_accounts = asset.depreciation_line_ids.mapped('account_depreciation_expense_id') | asset.account_depreciation_expense_id
                asset_depreciation = sum(
                    move.line_ids.filtered(
                        lambda l: l.account_id.internal_group == account_internal_group \
                            or l.account_id in asset_expense_accounts
                    ).mapped('balance')
                ) * (-1 if asset.asset_type == 'sale' else 1)
                # Special case of closing entry - only disposed assets of type 'purchase' should match this condition
                # The condition on len(move.line_ids) is to avoid the case where there is only one depreciation move, and it is not a disposal move
                # The condition will be matched because a disposal move from a disposal move will always have more than 2 lines, unlike a normal depreciation move
                if any(
                    line.account_id == asset.account_asset_id
                    and float_compare(-line.balance, asset.original_value, precision_rounding=asset.currency_id.rounding) == 0
                    for line in move.line_ids
                ) and len(move.line_ids) > 2:
                    asset_depreciation = (
                        asset.original_value
                        - asset.salvage_value
                        - (
                            move.line_ids[1].debit if asset.original_value > 0 else move.line_ids[1].credit
                        ) * (-1 if asset.original_value < 0 else 1)
                    )
            else:
                asset_depreciation = 0
            move.depreciation_value = asset_depreciation

    def _inverse_depreciation_value(self):
        sale_allocation = self.filtered(lambda r: r.asset_type == 'sale')
        for move in (self - sale_allocation):
            asset = move.asset_id
            amount = abs(move.depreciation_value)
            vals = []
            total_debit = 0
            for line in asset.depreciation_line_ids:
                account = line.account_depreciation_expense_id
                value = line.percentage
                debit = float_round(
                    value * amount / 100,  precision_rounding=asset.currency_id.rounding)
                vals += [
                    Command.update(line.id, {
                        'balance': debit if line.account_id == account else -amount,
                    })
                    for line in move.line_ids
                ]
                total_debit += debit
            if float_compare(amount, total_debit, precision_rounding=asset.currency_id.rounding) != 0:
                balance = vals[-1][1]['balance']
                balance += amount - total_debit
                vals[-1][1]['balance'] = balance
            move.write({'line_ids': vals})

        for move in sale_allocation:
            asset = move.asset_id
            amount = abs(move.depreciation_value)
            account = asset.account_depreciation_expense_id
            move.write({'line_ids': [
                Command.update(line.id, {
                    'balance': -amount if line.account_id == account else amount,
                })
                for line in move.line_ids
            ]})

    @api.depends('line_ids.asset_ids', 'line_ids.approval_move_asset_ids', 'asset_id')
    def _compute_asset_ids(self):
        def _get_asset_id_display_name(asset):
            if asset.asset_type == 'sale':
                asset_id_display_name = _('Deferred Revenue')
            elif asset.asset_type == 'expense':
                asset_id_display_name = _('Deferred Expense')
            else:
                asset_id_display_name = _('Asset')
            return asset_id_display_name

        super()._compute_asset_ids()
        for record in self:
            asset_id_display_name = _get_asset_id_display_name(record.asset_id)

            # Will happen if the move is not posted yet
            if not record.line_ids.asset_ids and record.line_ids.approval_move_asset_ids:
                record.asset_ids = record.line_ids.approval_move_asset_ids
                record.count_asset = len(record.asset_ids)
                record.draft_asset_exists = bool(
                    record.asset_ids.filtered(lambda x: x.state == "draft"))
                asset_id_display_name = _get_asset_id_display_name(
                    record.asset_ids[:1])
            asset = record.asset_id or record.asset_ids[:1]
            record.linked_asset_type = asset.asset_type
            record.asset_id_display_name = asset_id_display_name

    def action_post(self):
        result = super().action_post()
        for asset in self.env['account.asset'].search([('move_line_ids', 'in', self.invoice_line_ids.ids)]):
            asset.write({'original_move_line_ids': [
                        (6, 0, asset.move_line_ids.ids)]})
        return result

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.invoice_line_ids.create_deferred_assets()
        return result

    def _prepare_move_line_for_asset_depreciation(self, debit, credit, amount_currency, move_line_expense, depreciation_line):
        account = depreciation_line.account_depreciation_expense_id
        if not account:
            raise UserError(
                _('Please set up Expense Account'))
        analytic_expense_line = move_line_expense.copy()
        analytic_expense_line.update({
            'credit': credit,
            'debit': debit,
            'amount_currency': amount_currency,
            'account_id': account.id,
            'analytic_distribution': {depreciation_line.analytic_account_id.id: 100}
        })
        return analytic_expense_line

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        period_closing = self.env['accounting.period.closing']._get_current_accounting_period(
        )
        from_date = start_of(period_closing.accounting_period, 'month')
        end_date = end_of(period_closing.accounting_period, 'month')
        asset = vals['asset_id']
        if asset.asset_type == 'sale':
            new_amount = vals['amount'] * -1
            vals['amount'] = new_amount
        move_vals = super()._prepare_move_for_asset_depreciation(vals)

        # Flag for keeping original date
        if not self.env.context.get('keep_original_date') and move_vals['date'] < from_date:
            move_vals['date'] = end_date
        asset = vals['asset_id']
        move_line_depreciation = move_vals['line_ids'][0]
        move_line_depreciation[2]['analytic_distribution'] = False
        move_line_expense = move_vals['line_ids'][1][2].copy()
        move_vals['line_ids'] = [move_line_depreciation]

        # FIX: if no analytic distribution lines, keep original expense line
        lines = asset.depreciation_line_ids
        if not lines:
            move_vals['line_ids'] += [(0, 0, move_line_expense)]
            return move_vals

        total_debit = 0
        total_debit_currency = 0
        total_credit = 0
        for line in lines[:-1]:
            value = line.percentage
            credit = float_round(
                move_line_expense['credit'] * value / 100, precision_rounding=asset.currency_id.rounding)
            debit = float_round(
                move_line_expense['debit'] * value / 100, precision_rounding=asset.currency_id.rounding)
            amount_currency = float_round(
                move_line_expense['amount_currency'] * value / 100, precision_rounding=asset.currency_id.rounding)
            analytic_expense_line = self._prepare_move_line_for_asset_depreciation(
                debit, credit, amount_currency, move_line_expense, line)
            move_vals['line_ids'] += [(0, 0, analytic_expense_line)]
            total_debit += debit
            total_credit += credit
            total_debit_currency += amount_currency

        if line := lines[-1]:
            debit = move_line_expense['debit'] - total_debit
            credit = move_line_expense['credit'] - total_credit
            amount_currency = move_line_expense['amount_currency'] - total_debit_currency
            # Ensure correct sign: positive for debit, negative for credit
            if debit:
                amount_currency = abs(amount_currency)
            elif credit:
                amount_currency = -abs(amount_currency)
            analytic_expense_line = self._prepare_move_line_for_asset_depreciation(
                debit, credit, amount_currency, move_line_expense, line)
            move_vals['line_ids'] += [(0, 0, analytic_expense_line)]
        return move_vals
