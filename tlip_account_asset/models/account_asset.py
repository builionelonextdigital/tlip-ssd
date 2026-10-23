from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, formatLang
from odoo.tools.date_utils import end_of, start_of
from odoo.addons.account_asset.models.account_asset import AccountAsset as AccountAssetBase

from dateutil.relativedelta import relativedelta


def _compute_board_amount(self, residual_amount, period_start_date, period_end_date, days_already_depreciated,
                              days_left_to_depreciated, residual_declining, start_yearly_period=None, total_lifetime_left=None,
                              residual_at_compute=None, start_recompute_date=None, is_rounding=True):
    def _get_max_between_linear_and_degressive(linear_amount):
        """
        Compute the degressive amount that could be depreciated and returns the biggest between it and linear_amount
        The degressive amount corresponds to the difference between what should have been depreciated at the end of
        the period and the residual_amount (to deal with rounding issues at the end of each month)
        """
        fiscalyear_dates = self.company_id.compute_fiscalyear_dates(period_end_date)
        days_in_fiscalyear = self._get_delta_days(fiscalyear_dates['date_from'], fiscalyear_dates['date_to'])

        degressive_total_value = residual_declining * (1 - self.method_progress_factor * self._get_delta_days(start_yearly_period, period_end_date) / days_in_fiscalyear)
        degressive_amount = residual_amount - degressive_total_value
        return self._degressive_linear_amount(residual_amount, degressive_amount, linear_amount)

    days_until_period_end = self._get_delta_days(self.paused_prorata_date, period_end_date)
    days_before_period = self._get_delta_days(self.paused_prorata_date, period_start_date + relativedelta(days=-1))
    days_before_period = max(days_before_period, 0)  # if disposed before the beginning of the asset for example
    number_days = days_until_period_end - days_before_period
    if float_is_zero(self.asset_lifetime_days, 2):
        return 0, 0

    # The amount to depreciate are computed by computing how much the asset should be depreciated at the end of the
    # period minus how much difference it is actually depreciated. It is done that way to avoid having the last move to take
    # every single small difference that could appear over the time with the classic computation method.
    if self.method == 'linear':
        if total_lifetime_left and float_compare(total_lifetime_left, 0, 2) > 0:
            computed_linear_amount = residual_amount - residual_at_compute * (1 - self._get_delta_days(start_recompute_date, period_end_date) / total_lifetime_left)
        else:
            computed_linear_amount = self._get_linear_amount(days_before_period, days_until_period_end, self.total_depreciable_value)
        amount = min(computed_linear_amount, residual_amount, key=abs)
    elif self.method == 'degressive':
        # Linear amount
        # We first calculate the total linear amount for the period left from the beginning of the year
        # to get the linear amount for the period in order to avoid big delta at the end of the period
        days_left_from_beginning_of_year = self._get_delta_days(start_yearly_period, period_start_date - relativedelta(days=1)) + days_left_to_depreciated
        expected_remaining_value_with_linear = residual_declining - residual_declining * self._get_delta_days(start_yearly_period, period_end_date) / days_left_from_beginning_of_year
        linear_amount = residual_amount - expected_remaining_value_with_linear

        amount = _get_max_between_linear_and_degressive(linear_amount)
    elif self.method == 'degressive_then_linear':
        if not self.parent_id:
            linear_amount = self._get_linear_amount(days_before_period, days_until_period_end, self.total_depreciable_value)
        else:
            # we want to know the amount before the reeval for the parent so the child can follow the same curve,
            # so it transitions from degressive to linear at the same moment
            parent_moves = self.parent_id.depreciation_move_ids.filtered(lambda mv: mv.date <= self.prorata_date).sorted(key=lambda mv: (mv.date, mv.id))
            parent_cumulative_depreciation = parent_moves[-1].asset_depreciated_value if parent_moves else self.parent_id.already_depreciated_amount_import
            parent_depreciable_value = parent_moves[-1].asset_remaining_value if parent_moves else self.parent_id.total_depreciable_value
            if self.currency_id.is_zero(parent_depreciable_value):
                linear_amount = self._get_linear_amount(days_before_period, days_until_period_end, self.total_depreciable_value)
            else:
                # To have the same curve as the parent, we need to have the equivalent amount before the reeval.
                # The child's depreciable value corresponds to the amount that is left to depreciate for the parent.
                # So, we use the proportion between them to compute the equivalent child's total to depreciate.
                # We use it then with the duration of the parent to compute the depreciation amount
                depreciable_value = self.total_depreciable_value * (1 + parent_cumulative_depreciation/parent_depreciable_value)
                linear_amount = self._get_linear_amount(days_before_period, days_until_period_end, depreciable_value) * self.asset_lifetime_days / self.parent_id.asset_lifetime_days

        amount = _get_max_between_linear_and_degressive(linear_amount)

    amount = max(amount, 0) if self.currency_id.compare_amounts(residual_amount, 0) > 0 else min(amount, 0)
    amount = self._get_depreciation_amount_end_of_lifetime(residual_amount, amount, days_until_period_end)

    # At this point:
    # - Regular periods return their normally computed (optionally rounded) amount.
    # - The last period will bypass this return (handled in _recompute_board),
    #   so this value is used ONLY for non-final periods.
    if is_rounding:
        amount = self.currency_id.round(amount)
    
    return number_days, amount

def _recompute_board(self, start_depreciation_date=False):
    self.ensure_one()
    # All depreciation moves that are posted
    posted_depreciation_move_ids = self.depreciation_move_ids.filtered(
        lambda mv: mv.state == 'posted' and not mv.asset_value_change
    ).sorted(key=lambda mv: (mv.date, mv.id))

    imported_amount = self.already_depreciated_amount_import
    residual_amount = self.value_residual - sum(self.depreciation_move_ids.filtered(lambda mv: mv.state == 'draft').mapped('depreciation_value'))
    if not posted_depreciation_move_ids:
        residual_amount += imported_amount
    residual_declining = residual_at_compute = residual_amount
    # start_yearly_period is needed in the 'degressive' and 'degressive_then_linear' methods to compute the amount when the period is monthly
    start_recompute_date = start_depreciation_date = start_yearly_period = start_depreciation_date or self.paused_prorata_date

    last_day_asset = self._get_last_day_asset()
    final_depreciation_date = self._get_end_period_date(last_day_asset)
    total_lifetime_left = self._get_delta_days(start_depreciation_date, last_day_asset)

    depreciation_move_values = []
    rounded_so_far = 0.0

    fixed_monthly_amount = None
    has_posted_moves = bool(posted_depreciation_move_ids)

    # Equal monthly only for original untouched asset
    is_original_asset = not self.parent_id and not self.children_ids

    if (
        self.method == 'linear'
        and self.method_number
        and not has_posted_moves
        and not self.asset_modify_cr_ids
        and is_original_asset
    ):
        fixed_monthly_amount = self.currency_id.round(
            self.original_value / self.method_number
        )
    if not float_is_zero(self.value_residual, precision_rounding=self.currency_id.rounding):
        while not self.currency_id.is_zero(residual_amount) and start_depreciation_date < final_depreciation_date:
            period_end_depreciation_date = self._get_end_period_date(start_depreciation_date)
            period_end_fiscalyear_date = self.company_id.compute_fiscalyear_dates(period_end_depreciation_date).get('date_to')
            lifetime_left = self._get_delta_days(start_depreciation_date, last_day_asset)
            
            # Determine if this is the final depreciation period:
            # We compare current period end with the asset’s final depreciation period end.
            is_last_period = (period_end_depreciation_date == self._get_end_period_date(last_day_asset))
            is_first_period = start_depreciation_date == self.prorata_date
            if is_last_period:
                # Final period logic:
                # Instead of using _compute_board_amount (which may still contain rounding noise),
                # the last depreciation amount is force-calculated as:
                #     total_original_value − sum_of_all_prior_rounded_amounts
                amount = self.value_residual - rounded_so_far
                days = lifetime_left
            
            # Fixed monthly amount path (only for linear method with monthly depreciation):
            elif fixed_monthly_amount:
                if is_first_period:
                    # Pro-rata first month: fixed_monthly_amount × actual_days / days_in_month
                    days_in_month = period_end_depreciation_date.day
                    actual_days = period_end_depreciation_date.day - start_depreciation_date.day + 1
                    amount = fixed_monthly_amount * actual_days / days_in_month
                else:
                    amount = fixed_monthly_amount
                days = self._get_delta_days(start_depreciation_date, period_end_depreciation_date)
            
            else:
                # Non-final periods:
                # Compute unrounded amount (rounding=False), subtract from residual,
                # and accumulate rounded amounts separately. Rounding is ONLY applied
                # to the stored schedule, not to the internal residual math.
                days, amount = self._compute_board_amount(
                    residual_amount, start_depreciation_date, period_end_depreciation_date, False,
                    lifetime_left, residual_declining, start_yearly_period, total_lifetime_left,
                    residual_at_compute, start_recompute_date, is_rounding=False
                )
                residual_amount -= amount

            if not posted_depreciation_move_ids:
                # self.already_depreciated_amount_import management.
                # Subtracts the imported amount from the first depreciation moves until we reach it
                # (might skip several depreciation entries)
                if abs(imported_amount) <= abs(amount):
                    amount -= imported_amount
                    imported_amount = 0
                else:
                    imported_amount -= amount
                    amount = 0

            if self.method == 'degressive_then_linear' and final_depreciation_date < period_end_depreciation_date:
                period_end_depreciation_date = final_depreciation_date

            if not float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                # For deferred revenues, we should invert the amounts.
                depreciation_move_values.append(self.env['account.move']._prepare_move_for_asset_depreciation({
                    'amount': amount,
                    'asset_id': self,
                    'depreciation_beginning_date': start_depreciation_date,
                    'date': period_end_depreciation_date,
                    'asset_number_days': days,
                }))

                # Accumulate rounded amounts
                rounded_so_far += self.currency_id.round(amount)


            if period_end_depreciation_date == period_end_fiscalyear_date:
                start_yearly_period = self.company_id.compute_fiscalyear_dates(period_end_depreciation_date).get('date_from') + relativedelta(years=1)
                residual_declining = residual_amount

            start_depreciation_date = period_end_depreciation_date + relativedelta(days=1)

    return depreciation_move_values


# Apply patch
AccountAssetBase._compute_board_amount = _compute_board_amount
AccountAssetBase._recompute_board = _recompute_board


class AccountAssetDepreciationLine(models.Model):
    _name = 'account.asset.depreciation.line'

    account_depreciation_expense_id = fields.Many2one(
        comodel_name='account.account',
        string='Expense Account',
        required=True,
        check_company=True,
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance')), ('deprecated', '=', False)]",
        help="Account used in the periodical entries, to record a part of the asset as expense.",
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account', required=True,)
    percentage = fields.Float()
    asset_id = fields.Many2one(
        'account.asset', required=True, ondelete='cascade')


class AccountAssets(models.Model):
    _name = 'account.asset'
    _inherit = ["account.asset", "approval.matrix.mixin"]

    asset_type = fields.Selection([
        ('sale', 'Deferred Revenue'),
        ('expense', 'Deferred Expense'),
        ('fixed_asset', 'Fixed Asset')],
        index=True, copy=True, default='fixed_asset')

    cancel_reason = fields.Text(
        string='Reason for Cancellation', readonly=True, tracking=True)
    approval_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
        ],
        default="draft", tracking=True, copy=False,
    )
    approval_readonly = fields.Boolean(compute="_compute_approval_readonly")
    prorata_end_date = fields.Date(
        string='Prorata End Date', compute='_compute_prorata_end_date', readonly=False, store=True)

    asset_quantity = fields.Integer(default=1)
    asset_purchase_date = fields.Date(default=fields.Date.today())
    asset_supplier_id = fields.Many2one('res.partner')
    image = fields.Image('Asset Image', attachment=True, copy=False)

    # relational fields
    product_id = fields.Many2one(
        'product.product', domain="[('type', '=', 'consu')]")
    asset_code = fields.Char(string='Asset Code', copy=False)
    account_depreciation_expense_ids = fields.Many2many(
        comodel_name='account.account',
        string='Expense Accounts',
        compute='_compute_account_depreciation_expense_ids',
        store=True,
        check_company=True,
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance')), ('deprecated', '=', False)]",
    )
    move_line_ids = fields.Many2many(
        'account.move.line', 'asset_stock_move_line_rel', 'asset_id', 'sml_id', string='Move Lines')
    asset_modify_cr_ids = fields.One2many(
        'asset.modify.cr', 'asset_id', string='Asset Modify CRs')
    depreciation_line_ids = fields.One2many(
        'account.asset.depreciation.line', 'asset_id', 'Expense Account')
    revaluation_reason_id = fields.Many2one(
        'asset.revaluation.reason',
        default=lambda self: self.env.ref('tlip_account_asset.asset_revaluation_reason_other_increase',
                                          raise_if_not_found=False))

    @api.constrains("depreciation_line_ids")
    def _check_analytic_distribution(self):
        for record in self.filtered(lambda asset: asset.state != 'model'):
            if record.depreciation_line_ids and sum([line.percentage for line in record.depreciation_line_ids]) != 100:
                raise UserError(
                    _("The total of Analytic Distribution must be 100%"))

            if not record.account_depreciation_expense_ids:
                raise ValidationError(
                    _("Missing default account on budget code"))

    @api.depends('depreciation_line_ids')
    def _compute_account_depreciation_expense_ids(self):
        for record in self:
            record.account_depreciation_expense_ids = [
                (6, 0, record.mapped('depreciation_line_ids.account_depreciation_expense_id').ids)]

    @api.depends('prorata_date', 'method_number', 'method_period')
    def _compute_prorata_end_date(self):
        for record in self:
            record.prorata_end_date = record.prorata_date + \
                relativedelta(months=int(record.method_period)
                              * record.method_number)

    @api.depends('method_number', 'method_period', 'prorata_computation_type')
    def _compute_lifetime_days(self):
        prorata_day_assets = self.filtered(
            lambda r: not r.parent_id and r.prorata_end_date and r.prorata_computation_type == 'daily_computation')
        super(AccountAssets, self - prorata_day_assets)._compute_lifetime_days()
        for asset in prorata_day_assets:
            asset.asset_lifetime_days = (
                asset.prorata_end_date - asset.prorata_date).days + 1

    def _compute_approval_readonly(self):
        for rec in self:
            approval_readonly = False
            if rec.state != 'draft' or rec.approval_state != 'draft':
                approval_readonly = True
            rec.approval_readonly = approval_readonly

    def _get_last_day_asset(self):
        this = self.parent_id if self.parent_id else self
        if this.prorata_computation_type == 'daily_computation':
            return this.prorata_end_date
        return super()._get_last_day_asset()

    def action_save_model(self):
        action = super().action_save_model()
        if self.asset_type:
            form_ref = {
                'sale': 'tlip_account_asset.view_account_asset_revenue_form',
                'expense': 'tlip_account_asset.view_account_asset_expense_form',
                'fixed_asset': 'account_asset.view_account_asset_form',
            }.get(self.asset_type)
            action['views'] = [[self.env.ref(form_ref).id, "form"]]
            context = action.get('context')
            context.update({
                'default_asset_type': self.asset_type,
                'default_asset_code': self.asset_code,
                'default_asset_group_id': self.asset_group_id.id,
            })
            action.update({
                'views': [[self.env.ref(form_ref).id, "form"]],
                'context': context
            })
        return action

    def action_asset_modify(self):
        """ Returns an action opening the asset modification wizard.
        """
        action = super().action_asset_modify()

        # Find existing CR
        existing_cr = self.asset_modify_cr_ids.filtered_domain(
            [('state', '!=', 'completed')])
        if existing_cr:
            raise UserError(
                _('There is an ongoing modification request for this asset. Please complete the existing request before creating a new one.'))

        if self.asset_type:
            wizard = self.env['asset.modify'].browse(action['res_id'])
            wizard.write({'modify_action': 'modify'})
            if self.asset_type == 'sale':
                name = _('Modify Revenue')
            elif self.asset_type == 'fixed_asset':
                name = _('Modify Asset')
            else:
                name = _('Modify Expense')
            action['name'] = name
        return action

    def set_to_draft(self):
        self.action_reset_approval()
        return super().set_to_draft()

    def action_reset_approval(self):
        "Approval State: Rejected | Withdrawn -> Draft"
        self.write({"approval_state": "draft"})

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action["context"]["default_name"] = _(
            f"Approval Request for {self.name}"
        )
        return action

    def action_view_journal_entries(self):
        self.ensure_one()
        if self.asset_type == "expense":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_in_invoice_type")
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_out_invoice_type")
        action.update({'context': {'create': False, 'delete': False}})

        moves = self.move_line_ids.move_id
        if len(moves) == 1:
            action.update({
                'views': [(False, 'form')],
                'res_id': moves[:1].id,
            })
        else:
            action.update({
                'domain': [('id', 'in', moves.ids)],
            })
        return action

    def _trigger_action_approve(self):
        today = fields.Date.today()
        for asset in self:
            group = asset.asset_group_id
            vals = {'approval_state': 'approved'}
            if asset.asset_type == 'fixed_asset':
                if not (group and group.asset_prefix):
                    raise UserError(
                        _("Asset group's prefix has not been configured. Please update in Asset Group.")
                    )

                seq = group._get_or_create_sequence()
                if not seq:
                    raise UserError(
                        _("Unable to generate asset code. Please check the sequence configuration.")
                    )
                seq_val = seq.with_context(sequence_date=today).next_by_id()
                vals['asset_code'] = '%s%s' % (group.asset_prefix, seq_val)
            asset.write(vals)

    def _trigger_action_refuse(self):
        self.write({'approval_state': 'rejected'})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({'approval_state': 'wait_for_approval'})
        return result

    def _trigger_action_withdraw(self, reason: str):
        self.write({'approval_state': 'withdrawn'})
        super()._trigger_action_withdraw(reason)

    def _validate_submit_approval(self):
        for asset in self:
            group = asset.asset_group_id
            if asset.asset_type == 'fixed_asset':
                if not group:
                    raise UserError(
                        _("Asset group has not been configured. Please update in Asset Group.")
                    )

                if not group.asset_prefix:
                    raise UserError(
                        _("Asset group's prefix has not been configured. Please update in Asset Group.")
                    )

    # def _cancel_future_moves(self, date):
    #     period_closing = self.env['accounting.period.closing']._get_current_accounting_period(
    #     )
    #     accouting_from_date = start_of(
    #         period_closing.accounting_period, 'month')
    #     for asset in self:
    #         obsolete_moves = asset.depreciation_move_ids.filtered(lambda m: m.state == 'draft' or (
    #             not m.reversal_move_ids
    #             and not m.reversed_entry_id
    #             and m.state == 'posted'
    #             and m.date >= accouting_from_date
    #         ))
    #         obsolete_moves._unlink_or_reverse()

    def set_to_cancelled(self):
        cancel_reason = self.env.context.get('cancel_reason')
        if not cancel_reason:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Cancel Asset'),
                'res_model': 'asset.cancel.wizard',
                'view_mode': 'form',
                'target': 'new',
                'view_id': self.env.ref('tlip_account_asset.view_asset_cancel_wizard_form').id,
                'context': {'active_id': self.id},
            }
        self.write({'cancel_reason': cancel_reason})
        return super().set_to_cancelled()

    def action_open_asset_modify_crs(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'tlip_account_asset.asset_modify_cr_action')
        modify_cr_ids = self.asset_modify_cr_ids

        if len(modify_cr_ids) == 1:
            action.update({
                'res_id': modify_cr_ids.id,
                'view_mode': 'form',
                'views': [(False, 'form')]
            })
        else:
            action['domain'] = [('asset_id', '=', self.id)]

        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'parent_id' in vals and vals['parent_id']:
                parent = self.browse(vals['parent_id'])
                depreciation_line_ids = []
                for line in parent.depreciation_line_ids:
                    depreciation_line_ids += [(0, 0, {
                        'account_depreciation_expense_id': line.account_depreciation_expense_id.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'percentage': line.percentage
                    })]
                vals.update({
                    'depreciation_line_ids': depreciation_line_ids,
                    'asset_type': parent.asset_type
                })
        return super().create(vals_list)

    def write(self, vals):
        if 'fixed_asset' in self.mapped('asset_type') and 'account_depreciation_expense_id' in vals:
            del vals['account_depreciation_expense_id']
        return super().write(vals)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        super()._onchange_model_id()
        model = self.model_id
        if model:
            self.asset_code = model.asset_code

    def action_recompute_depreciation_async(self):
        for asset in self:
            post_until_date = self.env.context.get('start_date')
            if post_until_date and isinstance(post_until_date, str):
                post_until_date = fields.Date.from_string(post_until_date)
            if not post_until_date:
                post_until_date = fields.Date.today()

            # reset moves
            moves = asset.depreciation_move_ids.sorted('date')

            for move in moves.filtered(lambda m: m.state == 'posted'):
                move.button_draft()

            asset.depreciation_move_ids.unlink()

            # recompute full board from prorata_date (keep original dates)
            board_start = asset.prorata_date or asset.acquisition_date
            depreciation_move_values = asset.with_context(keep_original_date=True)._recompute_board(board_start)
            new_moves = self.env['account.move'].create(depreciation_move_values)

            # open and approved asset before posting moves
            if asset.state == 'draft':
                asset.write({'state': 'open', 'approval_state': 'approved'})

            # post moves up to post_until_date, one by one sorted by date
            moves_to_post = new_moves.filtered(
                lambda m: m.date <= post_until_date
            ).sorted('date')
            for move in moves_to_post:
                move.name = '/'
                move.with_context(
                    skip_accounting_period_check=True,
                    skip_date_sequence_check=True,
                )._post()


class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'

    asset_type = fields.Selection(related="asset_id.asset_type")
    revaluation_reason_id = fields.Many2one('asset.revaluation.reason')

    def custom_modify(self):
        period_closing = self.env['accounting.period.closing']._get_current_accounting_period(
        )
        accouting_from_date = start_of(
            period_closing.accounting_period, 'month')
        accouting_end_date = end_of(period_closing.accounting_period, 'month')

        modify_date = self.date if accouting_from_date <= self.date else accouting_from_date

        old_values = {
            'method_number': self.asset_id.method_number,
            'method_period': self.asset_id.method_period,
            'value_residual': self.asset_id.value_residual,
            'salvage_value': self.asset_id.salvage_value,
        }

        depreciation_line = self.asset_id.depreciation_line_ids.filtered(
            'account_depreciation_expense_id')[:1]
        expense_account = (
            self.account_depreciation_expense_id
            or depreciation_line.account_depreciation_expense_id
        )

        asset_vals = {
            'method_number': self.method_number,
            'method_period': self.method_period,
            'salvage_value': self.salvage_value,
            'account_asset_id': self.account_asset_id,
            'account_depreciation_id': self.account_depreciation_id,
            'account_depreciation_expense_id': expense_account,
        }
        if self.env.context.get('resume_after_pause'):
            date_before_pause = max(self.asset_id.depreciation_move_ids,
                                    key=lambda x: x.date).date if self.asset_id.depreciation_move_ids else self.asset_id.acquisition_date
            # We are removing one day to number days because we don't count the current day
            # i.e. If we pause and resume the same day, there isn't any gap whereas for depreciation
            # purpose it would count as one full day
            number_days = self.asset_id._get_delta_days(
                date_before_pause, self.date) - 1
            if self.currency_id.compare_amounts(number_days, 0) < 0:
                raise UserError(
                    _("You cannot resume at a date equal to or before the pause date"))

            asset_vals.update(
                {'asset_paused_days': self.asset_id.asset_paused_days + number_days})
            asset_vals.update({'state': 'open'})
            self.asset_id.message_post(body=_("Asset unpaused. %s", self.name))
        current_asset_book = self.asset_id._get_own_book_value(
            self.date)  # self.date
        after_asset_book = self._get_own_book_value()
        increase = after_asset_book - current_asset_book

        new_residual, new_salvage = self._get_new_asset_values(
            current_asset_book)
        residual_increase = max(0, self.value_residual - new_residual)
        salvage_increase = max(0, self.salvage_value - new_salvage)

        if not self.env.context.get('resume_after_pause'):
            if self.env['account.move'].search_count([('asset_id', '=', self.asset_id.id), ('state', '=', 'draft'), ('date', '<=', self.date)], limit=1):
                raise UserError(
                    _('There are unposted depreciations prior to the selected operation date, please deal with them first.'))
            self.asset_id._create_move_before_date(self.date)

        asset_vals.update({
            'salvage_value': new_salvage,
        })
        computation_children_changed = (
            asset_vals['method_number'] != self.asset_id.method_number
            or asset_vals['method_period'] != self.asset_id.method_period
            or asset_vals.get('asset_paused_days') and not float_is_zero(asset_vals['asset_paused_days'] - self.asset_id.asset_paused_days, 8)
        )
        self.asset_id.write(asset_vals)

        # Check for residual/salvage increase while rounding with the company currency precision to prevent float precision issues.
        if self.currency_id.compare_amounts(residual_increase + salvage_increase, 0) > 0:
            if not expense_account:
                raise UserError(
                    _("Please set up Expense Account on the asset depreciation lines.")
                )
            move = self.env['account.move'].create({
                'journal_id': self.asset_id.journal_id.id,
                'date': accouting_from_date + relativedelta(days=1),
                'move_type': 'entry',
                'asset_move_type': 'positive_revaluation',
                'line_ids': [
                    Command.create({
                        'account_id': self.account_asset_id.id,
                        'debit': residual_increase + salvage_increase,
                        'credit': 0,
                        'name': _('Value increase for: %(asset)s', asset=self.asset_id.name),
                    }),
                    Command.create({
                        'account_id': self.account_asset_counterpart_id.id,
                        'debit': 0,
                        'credit': residual_increase + salvage_increase,
                        'name': _('Value increase for: %(asset)s', asset=self.asset_id.name),
                    }),
                ],
            })
            move._post()
            asset_increase = self.env['account.asset'].create({
                'name': self.asset_id.name + ': ' + self.name if self.name else "",
                'currency_id': self.asset_id.currency_id.id,
                'company_id': self.asset_id.company_id.id,
                'method': self.asset_id.method,
                'method_number': self.method_number,
                'method_period': self.method_period,
                'method_progress_factor': self.asset_id.method_progress_factor,
                'acquisition_date': self.date + relativedelta(days=1),
                'value_residual': residual_increase,
                'salvage_value': salvage_increase,
                'prorata_date': self.date + relativedelta(days=1),
                'prorata_computation_type': 'daily_computation' if self.asset_id.prorata_computation_type == 'daily_computation' else 'constant_periods',
                'original_value': self._get_increase_original_value(residual_increase, salvage_increase),
                'account_asset_id': self.account_asset_id.id,
                'account_depreciation_id': self.account_depreciation_id.id,
                'account_depreciation_expense_id': expense_account.id,
                'journal_id': self.asset_id.journal_id.id,
                'parent_id': self.asset_id.id,
                'original_move_line_ids': [(6, 0, move.line_ids.filtered(lambda r: r.account_id == self.account_asset_id).ids)],
            })
            asset_increase.validate()

            subject = _('A gross increase has been created: %(link)s',
                        link=asset_increase._get_html_link())
            self.asset_id.message_post(body=subject)

        if self.currency_id.compare_amounts(increase, 0) < 0:
            move = self.env['account.move'].create(self.env['account.move']._prepare_move_for_asset_depreciation({
                'amount': -increase,
                'asset_id': self.asset_id,
                'move_ref': _('Value decrease for: %(asset)s', asset=self.asset_id.name),
                'depreciation_beginning_date': self.date,
                'depreciation_end_date': self.date,
                'date': self.date,
                'asset_number_days': 0,
                'asset_value_change': True,
                'asset_move_type': 'negative_revaluation',
                'revaluation_reason_id': self.revaluation_reason_id.id if self.asset_id.asset_type else False,
            }))._post()
        restart_date = self.date if self.env.context.get(
            'resume_after_pause') else self.date + relativedelta(days=1)
        if self.asset_id.depreciation_move_ids:
            self.asset_id.compute_depreciation_board(restart_date)
        else:
            # We have no moves, we can compute it as new
            self.asset_id.compute_depreciation_board()

        if computation_children_changed:
            children = self.asset_id.children_ids
            children.write({
                'method_number': asset_vals['method_number'],
                'method_period': asset_vals['method_period'],
                'asset_paused_days': self.asset_id.asset_paused_days,
            })

            for child in children:
                if not self.env.context.get('resume_after_pause'):
                    child._create_move_before_date(self.date)
                if child.depreciation_move_ids:
                    child.compute_depreciation_board(restart_date)
                else:
                    child.compute_depreciation_board()
                child._check_depreciations()
                child.depreciation_move_ids.filtered(
                    lambda move: move.state != 'posted')._post()
        tracked_fields = self.env['account.asset'].fields_get(
            old_values.keys())
        changes, tracking_value_ids = self.asset_id._mail_track(
            tracked_fields, old_values)
        if changes:
            self.asset_id.message_post(body=_(
                'Depreciation board modified %s', self.name), tracking_value_ids=tracking_value_ids)
        self.asset_id._check_depreciations()
        self.asset_id.depreciation_move_ids.filtered(
            lambda move: move.state != 'posted')._post()
        return {'type': 'ir.actions.act_window_close'}

    def modify(self):
        if not self.env.context.get('tlip_custom_asset', False):
            res = super(AssetModify, self).modify()
        else:
            res = self.custom_modify()
        return res

    def button_confirm_asset_modify_cr(self):
        self.ensure_one()
        cr_id = self.env['asset.modify.cr'].create(
            self._prepare_asset_modify_cr_vals()
        )

        action = self.env["ir.actions.actions"]._for_xml_id(
            "tlip_account_asset.asset_modify_cr_action")
        action.update({
            'res_id': cr_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')]
        })
        return action

    def _prepare_asset_modify_cr_vals(self):
        cr_vals = self.copy_data()[0]
        cr_vals.update({'cr_name': self.asset_id.name + ' - Modify CR'})
        return cr_vals

    def sell_dispose(self):
        res = super(AssetModify, self).sell_dispose()
        disposal_moves = self.asset_id.depreciation_move_ids.filtered(
            lambda m: m.asset_move_type == 'disposal')
        if disposal_moves:
            disposal_moves.write(
                {'revaluation_reason_id': self.revaluation_reason_id.id})
        return res
