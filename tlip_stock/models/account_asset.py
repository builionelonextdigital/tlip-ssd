from ast import literal_eval

from odoo import api, models,fields, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    package_id = fields.Many2one(
        'stock.quant.package', string='Asset Code', copy=False
    )

    def action_view_related_stock_quants(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('stock.location_open_quants')

        context = dict(self.env.context)
        action.update({
            'target': 'current',
            'domain': [("asset_ids", "in", [self.id])],
            'context': context
        })

        return action
