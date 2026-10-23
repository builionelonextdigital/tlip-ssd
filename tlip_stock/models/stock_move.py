from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends('state', 'picking_id.is_locked', 'picking_id.picking_internal_code')
    def _compute_is_initial_demand_editable(self):
        super()._compute_is_initial_demand_editable()
        self.filtered(lambda rec: rec.picking_id.picking_internal_code == 'inspect').update({
            'is_initial_demand_editable': False
        })

    @api.depends('product_id', 'picking_id.picking_internal_code')
    def _compute_is_quantity_done_editable(self):
        super()._compute_is_quantity_done_editable()
        self.filtered(lambda rec: rec.picking_id.picking_internal_code == 'inspect').update({
            'is_quantity_done_editable': False
        })

    def copy_data(self, default=None):
        inspect_moves = self.filtered(lambda rec: rec.picking_id.picking_internal_code == 'inspect')
        new_inspect_moves = super(StockMove, inspect_moves).copy_data({**(default or {}), "product_uom_qty": 0})
        new_other_moves = super(StockMove, (self - inspect_moves)).copy_data(default)
        return new_inspect_moves + new_other_moves

    def _prepare_inspect_move_line_vals(self):
        self.ensure_one()
        product = self.product_id
        move_line_vals = []
        src_quants = self.env["stock.quant"].search([
            ("product_id", "=", product.id),
            ("location_id", "child_of", self.location_id.ids)
        ])
        for quant in src_quants:
            # With the package having stock serial
            product_stock_serials = quant.package_id.stock_serial_ids.filtered_domain([('product_id', '=', quant.product_id.id)])
            for stock_serial in product_stock_serials:
                ml_vals = self._prepare_move_line_vals(quantity=1, reserved_quant=quant)
                ml_vals["result_package_id"] = ml_vals.get("package_id", False)
                ml_vals["qr_code"] = stock_serial.qr_code
                ml_vals["barcode"] = stock_serial.display_name
                ml_vals["location_dest_id"] = quant.location_id.id
                ml_vals["inspect_qty"] = 1
                move_line_vals.append((0, 0, ml_vals))

            # With the quant that does not have package or no stock serial
            remaining_qty = quant.quantity - len(product_stock_serials)
            if remaining_qty > 0:
                ml_vals = self._prepare_move_line_vals(quantity=remaining_qty, reserved_quant=quant)
                ml_vals["location_dest_id"] = quant.location_id.id
                ml_vals["result_package_id"] = ml_vals.get("package_id", False)
                ml_vals["qr_code"] = product.qr_code
                ml_vals["barcode"] = product.barcode
                ml_vals["inspect_qty"] = remaining_qty
                move_line_vals.append((0, 0, ml_vals))

        return move_line_vals, sum(src_quants.mapped("quantity"))

    def _check_and_allocate_to_virtual_location(self):
        self.ensure_one()
        move_line_vals = []
        virtual_location = self.env["stock.location"].search(
            [('usage', '=', 'inventory')], limit=1)
        for line in self.move_line_ids:
            quantity = line.inspect_qty
            if line.qty_done < quantity:
                if (quantity == 1) or (line.qty_done == 0):
                    move_line_vals.append((1, line.id, {"location_dest_id": virtual_location.id, "result_package_id": False, "picked": True}))
                else:
                    remaining_qty = quantity - line.qty_done
                    copy_vals = line.copy_data({
                        "location_dest_id": virtual_location.id,
                        "result_package_id": False,
                        "quantity": remaining_qty,
                    })
                    move_line_vals.append((1, line.id, {"quantity": line.qty_done}))
                    move_line_vals.extend((0, 0, vals) for vals in copy_vals)
            else:
                move_line_vals.append((1, line.id, {"quantity": line.qty_done}))
        return move_line_vals

    # def _get_assets_from_stock_move_and_stock_quants(self, quants):
    #     self.ensure_one()
    #     """Filter stock quants based on the stock move line's product and location."""
    #     ml_packages = self.move_line_ids.package_id
    #     have_empty_package = ml_packages and any(not package for package in ml_packages)
    #     quant_domain = [
    #         ("product_id", "=", self.product_id.id),
    #         ("location_id", "=", self.location_id.id),
    #         ("package_id", "in", ml_packages.ids + \
    #                                 ([False] if have_empty_package else [])),
    #     ]

    #     if self.lot_ids:
    #         quant_domain.append(("lot_id", "in", self.lot_ids.ids))
    #     return quants.filtered_domain(quant_domain).asset_ids

    # def search_related_stock_quants(self, is_source=True):
    #     """Search for stock quants related to the products and locations of the stock moves."""
    #     if is_source:
    #         quant_packages = self.move_line_ids.package_id
    #         location_id = self.location_id
    #     else:
    #         quant_packages = self.move_line_ids.result_package_id
    #         location_id = self.location_dest_id

    #     have_empty_package = quant_packages and any(not package for package in quant_packages)
    #     quant_domain = [
    #         ("product_id", "in", self.product_id.ids),
    #         ("location_id", "in", location_id.ids),
    #         ("lot_id", "in", self.lot_ids.ids + [False]),
    #         ("package_id", "in", quant_packages.ids + \
    #                                 ([False] if have_empty_package else [])),
    #     ]
    #     return self.env['stock.quant'].search(quant_domain)

    def _generate_valuation_lines_data(
        self,
        partner_id,
        qty,
        debit_value,
        credit_value,
        debit_account_id,
        credit_account_id,
        svl_id,
        description,
    ):
        vals = super()._generate_valuation_lines_data(
            partner_id,
            qty,
            debit_value,
            credit_value,
            debit_account_id,
            credit_account_id,
            svl_id,
            description,
        )
        analytic_distribution = self.picking_id.analytic_distribution
        vals["credit_line_vals"].update({
            "analytic_distribution": analytic_distribution,
        })
        vals["debit_line_vals"].update({
            "analytic_distribution": analytic_distribution,
        })
        return vals


    def _get_dest_account(self, accounts_data):
        if self.location_dest_id.is_exported_for_use:
            # Get the default account from the budget code of the analytic account, replace the dest account from location
            analytic_account = self.picking_id.distribution_analytic_account_ids[0]
            budget_code = analytic_account.budget_code_id.with_context(company_id=self.company_id.id)
            account = budget_code.default_account_id
            if not account:
                raise UserError(_("Please set Default Account in Budget Code %s") % budget_code.display_name)
            return account.id

        return super()._get_dest_account(accounts_data)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    inspect_qty = fields.Integer()
    usage = fields.Char()
    is_result_package_required = fields.Boolean(compute="_compute_is_result_package_required")
    qr_code = fields.Binary()
    barcode = fields.Char()
    result_package_id = fields.Many2one(
        'stock.quant.package', 'Destination Asset Code',
        ondelete='restrict', required=False, check_company=True,
        domain="['|', ('id', '=', package_id), '&', ('quant_ids', '=', False), '|', ('location_id', '=', False), ('location_id', '=', location_dest_id)]")
    package_id = fields.Many2one(
        'stock.quant.package', 'Source Asset Code')
    asset_id = fields.Many2one(
        'account.asset', string='Related Assets', compute="_compute_asset_id", store=True
    )

    @api.depends("picking_id")
    def _compute_is_result_package_required(self):
        for rec in self:
            picking = rec.picking_id
            rec.is_result_package_required = picking.picking_internal_code != "inspect"

    @api.depends("result_package_id", "package_id")
    def _compute_asset_id(self):
        for rec in self:
            if rec.result_package_id == rec.package_id:
                rec.asset_id = rec.package_id.asset_ids[:1]

    @api.onchange("quant_id")
    def _onchange_quant_id(self):
        """When a quant is selected, set the package_id immediately, to apply domain for result_package_id."""
        self.package_id = self.quant_id.package_id
        if self.result_package_id and self.result_package_id != self.package_id and self.result_package_id.quant_ids:
            self.result_package_id = False

    def _action_done(self):
        for line in self:
            line.result_package_id.write({"usage": line.usage})
            line.asset_id.write({"package_id": line.result_package_id.id})

        res = super()._action_done()

        return res

    @api.model
    def _get_fields_stock_barcode(self):
        return super()._get_fields_stock_barcode() + ['barcode']
