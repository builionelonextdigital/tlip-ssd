from odoo import models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    def _validate_accounting_entries(self):
        """
        Inherit _validate_accounting_entries and generate account move for case product category is manual periodic and is_exported_for_use location
        Create account.move for stock.valuation.layer and do not _post, wait accounting to submit
        """
        am_vals = []
        for svl in self:
            if not svl.with_company(svl.company_id).product_id.valuation == "manual_periodic":
                continue
            picking = svl.stock_move_id.picking_id
            if not (picking.location_dest_id and picking.location_dest_id.is_exported_for_use):
                continue
            if svl.currency_id.is_zero(svl.value):
                continue
            move = svl.stock_move_id
            if not move:
                move = svl.stock_valuation_layer_id.stock_move_id
            am_vals += move.with_company(svl.company_id)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
        if am_vals:
            self.env['account.move'].sudo().create(am_vals)

        return super()._validate_accounting_entries()
