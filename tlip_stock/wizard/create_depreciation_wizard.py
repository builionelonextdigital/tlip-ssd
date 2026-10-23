from ast import literal_eval

from odoo import _, api, fields, models
from odoo.tools import groupby
from odoo.exceptions import UserError


class CreateDepreciationWizard(models.TransientModel):
    _name = 'create.depreciation.wizard'
    _description = 'Depreciation'

    wizard_line_ids = fields.One2many(
        "create.depreciation.wizard.line", "wizard_id",
    )

    def action_confirm(self):
        action = self.env['ir.actions.actions']._for_xml_id('account_asset.action_account_asset_form')
        assets = self.wizard_line_ids.generate_account_assets()

        context = literal_eval(action['context'])
        context.update({"create": 0})
        action.update({
            'domain': [('id', 'in', assets.ids)],
            'context': context
        })
        return action


class CreateDepreciationWizardLine(models.TransientModel):
    _name = 'create.depreciation.wizard.line'
    _description = 'Create Asset Depreciation Line'

    wizard_id = fields.Many2one(
        'create.depreciation.wizard',
        required=True
    )
    move_line_id = fields.Many2one('stock.move.line', required=True)
    product_id = fields.Many2one('product.product', related='move_line_id.product_id')
    quantity = fields.Float(related='move_line_id.quantity')
    price_unit = fields.Float(related='product_id.standard_price')
    result_package_id = fields.Many2one(
        'stock.quant.package', related='move_line_id.result_package_id'
    )
    is_multiple_asset = fields.Boolean(
        string="Asset Depreciation per Qty",
        help="If check field 'Asset Depreciation per Qty' then the system will generate asset depending on stock move quantity instead of global asset"
    )

    def generate_account_assets(self):
        AccountAsset = self.env['account.asset']
        for line in self:
            account_asset_vals = line._prepare_account_asset_vals()
            asset_id = AccountAsset.create(account_asset_vals)
            line.move_line_id.write({"asset_id": asset_id})
        return self.move_line_id.asset_id

    def _prepare_account_asset_vals(self):
        self.ensure_one()
        price = self.price_unit
        expense_account = self.product_id.categ_id.property_account_expense_categ_id
        asset_vals = {
            "name": self.product_id.name,
            "account_depreciation_id": expense_account.id,
            "original_value": price * self.quantity,
        }

        if expense_account.account_type == "asset_prepayments":
            asset_vals.update({"asset_type": "expense"})

        return asset_vals
