from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move.line"

    approval_move_asset_ids = fields.Many2many('account.asset', 'asset_approval_move_line_rel', 'line_id', 'asset_id', string='Related Assets', copy=False)
    asset_code = fields.Char(
        string='Asset Code',
        compute='_compute_asset',
        store=True, readonly=False
    )
    asset_name = fields.Char(
        string='Deferred Name',
        compute='_compute_asset',
        store=True, readonly=False
    )

    @api.depends("asset_ids", "asset_ids.asset_code", "asset_ids.name")
    def _compute_asset(self):
        for line in self:
            asset = line.asset_ids[:1]  # always provide recordset eventhough asset_ids is empty
            line.asset_code = asset.asset_code
            line.asset_name = asset.name

    def create_deferred_assets(self):
        """
            Sync deferred asset with the move line
            Odoo base was not allowed to link to assets if move line is not posted. Link to temporary assets, and lines then action post 
            will link to the real assets.
        """
        asset_vals = []
        for line in self:
            if line.deferred_start_date and line.deferred_end_date:
                asset_vals.append(line._prepare_deffered_asset_vals())

        for asset in self.env['account.asset'].create(asset_vals):
            asset.move_line_ids.write({'approval_move_asset_ids': [(6, 0, [asset.id])]})

    def _prepare_deffered_asset_vals(self):
        self.ensure_one()

        move_id = self.move_id
        vals = {
            'name': self.name,
            'move_line_ids': [(6, 0, [self.id])],
            'acquisition_date': move_id.invoice_date,
            'method_number': self._calculate_months_duration(self.deferred_start_date, self.deferred_end_date),
            'method_period': '1',
            'account_depreciation_id': self.account_id.id,
            'analytic_distribution': self.analytic_distribution,
            'original_value': self.balance,
        }

        if move_id.move_type in ['out_invoice', 'out_refund']:
            vals.update({
                'asset_type': 'sale',
                'account_depreciation_expense_id': self.product_id.property_account_income_id.id,
            })
        else:
            vals.update({
                'asset_type': 'expense',
                'account_depreciation_expense_id': self.product_id.property_account_expense_id.id,
            })

        return vals

    @api.model
    def _calculate_months_duration(self, start_date, end_date):
        """Calculate duration in months between two dates"""
        if not start_date or not end_date:
            return 0

        # Calculate full months difference including years
        r = relativedelta(end_date, start_date)
        total_months = r.years * 12 + r.months

        # If end date is not the same day of month as start date, add 1 month
        if end_date.day != start_date.day:
            total_months += 1

        return abs(total_months)
