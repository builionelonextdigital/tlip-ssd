from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import groupby, SQL

from contextlib import closing


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'approval.matrix.mixin', 'analytic.mixin']

    def _default_picking_type_id(self):
        picking_type_code = self.env.context.get('restricted_picking_type_code')
        internal_type_code = self.env.context.get('internal_type_code', False)
        if picking_type_code:
            picking_types = self.env['stock.picking.type'].search([
                ('code', '=', picking_type_code),
                ('company_id', '=', self.env.company.id),
                ('internal_code', '=', internal_type_code)
            ])
            return picking_types[:1].id

    picking_type_id = fields.Many2one(default=_default_picking_type_id)
    picking_internal_code = fields.Selection(
        related='picking_type_id.internal_code',
        readonly=True)
    available_location_dest_ids = fields.Many2many('stock.location', compute="_compute_available_location_dest_ids")
    asset_ids = fields.Many2many('account.asset', compute="_compute_display_fa_depreciation")
    is_wh_to_usage = fields.Boolean(compute="_compute_display_fa_depreciation")
    display_fa_depreciation = fields.Boolean(compute="_compute_display_fa_depreciation")
    is_ready_validate = fields.Boolean(compute='_compute_display_fa_depreciation')
    is_to_wh = fields.Boolean(compute="_compute_display_fa_depreciation")
    approval_readonly = fields.Boolean(compute="_compute_approval_readonly")
    is_exported_for_use = fields.Boolean(related='location_dest_id.is_exported_for_use')

    @api.depends("picking_type_id", "location_id", "location_dest_id", "move_ids.move_line_ids.asset_id", "move_ids.move_line_ids.package_id", "move_ids.product_id")
    def _compute_display_fa_depreciation(self):
        stock_locations = (self.location_id | self.location_dest_id).warehouse_id.lot_stock_id
        for rec in self:
            is_to_wh = rec.location_dest_id in stock_locations
            is_wh_to_usage = False
            is_ready_validate = True
            display_fa_depreciation = any(not line.asset_id for line in rec.move_ids.move_line_ids)
            asset_ids = rec.move_ids.move_line_ids.asset_id

            # TODO: Han to remove code relating to asset_ids
            # if rec.picking_internal_code in ["dispose", "damage", "maintenance", "internal"]:
            #     for move in rec.move_ids:
            #         asset_ids |= move.move_line_ids.package_id.asset_ids

            if rec.picking_internal_code == "internal":
                is_wh_to_usage = rec.location_id in stock_locations and rec.location_dest_id not in stock_locations
            elif rec.picking_type_code == "incoming":
                is_wh_to_usage = rec.location_dest_id not in stock_locations

            # if (display_fa_depreciation and not is_to_wh) or not all([asset.state != 'draft' for asset in asset_ids]):
            #     is_ready_validate = False

            rec.is_wh_to_usage = is_wh_to_usage
            rec.is_to_wh = is_to_wh
            rec.display_fa_depreciation = display_fa_depreciation
            rec.asset_ids = asset_ids
            rec.is_ready_validate = is_ready_validate

    @api.depends("picking_internal_code")
    def _compute_available_location_dest_ids(self):
        StockLocations = self.env['stock.location'].search([])
        for rec in self:
            if rec.picking_type_id:
                domain = rec.picking_type_id._get_domain_locations_internal_code()
                rec.available_location_dest_ids = StockLocations.filtered_domain(domain)
            else:
                rec.available_location_dest_ids = StockLocations

    def _compute_location_id(self):
        super()._compute_location_id()
        for picking in self.filtered(lambda rec: rec.picking_internal_code == "inspect"):
            picking.location_dest_id = picking.location_id

    def _compute_approval_readonly(self):
        for rec in self:
            approval_readonly = False
            if rec.state in ('done', 'cancel') or rec.approval_state != 'draft':
                approval_readonly = True
            rec.approval_readonly = approval_readonly

    @api.onchange("location_id")
    def _onchange_source_location(self):
        self.ensure_one()
        if self.picking_internal_code == "inspect":
            self.location_dest_id = self.location_id

        self.move_ids.location_id = self.location_id

    @api.onchange("location_dest_id")
    def _onchange_destination_location(self):
        self.ensure_one()
        if not self.is_exported_for_use:
            self.analytic_distribution = None

    def generate_product_transfer_sequence(self):
        for picking in self:
            if picking.state != 'done':
                raise UserError(_("Only generate QR with Done state"))
            if not picking.is_wh_to_usage:
                raise UserError(_("Only generate QR for transfer from Stock/Receipt to Location"))

        stock_serials = self.env["tlip.stock.serial"].create(self._prepare_stock_serial_vals())
        stock_serials._generate_qr_code()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("QR has been generated successfully"),
                'sticky': False,
                'type': 'info',
            }
        }

    def button_validate(self):
        if not self.env.context.get("submit_approval_validate") and any(picking.approval_state != 'approved' for picking in self):
            raise UserError(_("Do not allow to validate the transfer that is not approved."))
        self.filtered(lambda rec: rec.picking_internal_code == "inspect")._inspect_missing_qty_to_virtual_location()

        # for line in self.move_ids.move_line_ids:
        #     if line.result_package_id.quant_ids and line.result_package_id != line.package_id:
        #         raise UserError(_(
        #             f"Please check the asset code {line.result_package_id.name} in line {line.product_id.name}. The asset code already has products."))

        return super().button_validate()

    # def action_generate_asset_depreciation(self):
    #     self.ensure_one()

    #     depreciation_wizard_line_vals = [(5, 0, 0)] + self._prepare_depreciation_wizard_line_vals()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Depreciation'),
    #         'res_model': 'create.depreciation.wizard',
    #         'views': [(self.env.ref('tlip_stock.create_depreciation_wizard_view_form').id, 'form')],
    #         'target': 'new',
    #         'context': {
    #             "default_wizard_line_ids": depreciation_wizard_line_vals
    #         }
    #     }

    # def action_view_account_assets(self):
    #     self.ensure_one()
    #     action = self.env['ir.actions.actions']._for_xml_id('account_asset.action_account_asset_form')

    #     context = literal_eval(action['context'])
    #     context.update({"create": 0})

    #     action.update({
    #         'domain': [('id', 'in', self.asset_ids.ids)],
    #         'context': context
    #     })
    #     return action

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action['context']['default_name'] = _(
            f'Approval Request for Transfer {self.name}')
        return action

    def _prepare_stock_serial_vals(self):
        last_sequence_products = self._get_last_sequence_product_count_mapping()

        StockMoveLine = self.env["stock.move.line"]
        stock_serial_vals = []
        for (product, package), lines in groupby(sorted(self.move_line_ids, key=lambda l: (l.product_id.id, l.result_package_id.id)), lambda l: (l.product_id, l.result_package_id)):
            lines = StockMoveLine.concat(*lines)
            last_num = last_sequence_products.get(product.id, 0)
            product_quant_qty = sum(package.quant_ids.filtered(lambda quant, product_id=product.id: \
                                                                   quant.product_id.id == product_id).mapped("quantity"))
            product_qr_qty = len(package.stock_serial_ids.filtered(lambda serial, product_id=product.id: \
                                                                    serial.product_id.id == product_id))
            if product_quant_qty <= product_qr_qty:
                # Compare package product quantity and qr quantity
                continue

            added_qty = int(sum(lines.mapped("quantity")))
            starting_num = last_num + 1
            ending_num = starting_num + added_qty
            last_sequence_products[product.id] = last_num + added_qty

            stock_serial_vals.extend([{
                "package_id": package.id,
                "serial_number": serial_number,
                "product_id": product.id
            } for serial_number in range(starting_num, ending_num)])

        return stock_serial_vals

    def _get_last_sequence_product_count_mapping(self):
        sql_query = SQL(
            """
                SELECT product_id, max(serial_number)
                FROM tlip_stock_serial
                WHERE product_id in %(product_ids)s
                GROUP BY product_id
            """,
            product_ids=tuple(self.move_line_ids.product_id.ids)
        )
        self.env.cr.execute(sql_query)
        return {result["product_id"]: result["max"] for result in self.env.cr.dictfetchall()}

    # def _prepare_depreciation_wizard_line_vals(self):
    #     return [(0, 0, {
    #         "move_line_id": line.id
    #     }) for line in self.move_ids.move_line_ids if not line.asset_id and line.result_package_id]

    def _validate_submit_approval(self):
        # grouped_stock_quants = self._get_grouped_stock_quants()
        with closing(self.env.cr.savepoint()):
            for record in self:
                record.with_context(submit_approval_validate=True).button_validate()
                if not record.move_ids:
                    raise UserError(_(
                        "You can’t submit an empty transfer. Please add some products to move before proceeding."
                    ))

                # if record.picking_internal_code != "inspect":
                #     picking_type_code = record.picking_type_code

                #     for line in record.move_ids.move_line_ids:
                #         on_hand_qty = grouped_stock_quants.get((line.product_id, line.location_id, line.package_id), 0)
                #         if picking_type_code != 'incoming':
                #             if line.quantity > on_hand_qty:
                #                 raise UserError(_(f"Product ({line.product_id.name}) in source asset code ({line.package_id.name}) does not have enough demand quantity"))
                #             elif on_hand_qty:
                #                 grouped_stock_quants.update({
                #                     (line.product_id, line.location_id, line.package_id): on_hand_qty - line.quantity
                #                 })

                #     used_packages = set()
                #     for line in record.move_ids.move_line_ids:
                #         if line.result_package_id:
                #             if line.result_package_id in used_packages:
                #                 raise UserError(_(
                #                     "Not allowed to have the same asset code in the same transfer. "
                #                     "Please check the asset code in the transfer."
                #                 ))
                #             used_packages.add(line.result_package_id)

    def _trigger_action_approve(self):
        self.write({'approval_state': 'approved'})

    def _trigger_action_refuse(self):
        self.write({"approval_state": "rejected"})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.filtered(lambda rec: rec.picking_internal_code == "inspect")._update_inspect_qty()
        self.write({'approval_state': 'wait_for_approval'})
        return result

    def _trigger_action_withdraw(self, reason: str):
        self.write({'approval_state': 'withdrawn'})
        super()._trigger_action_withdraw(reason)

    def _update_inspect_qty(self):
        # trigger upon submit approval in inspect picking
        for move in self.move_ids:
            move_line_vals, demand_qty = move._prepare_inspect_move_line_vals()
            move.write({
                "move_line_ids": move_line_vals,
                "product_uom_qty": demand_qty
            })

    def _inspect_missing_qty_to_virtual_location(self):
        # trigger upon validate action in inspect picking
        for move in self.filtered(lambda rec: rec.picking_internal_code == 'inspect').move_ids:
            move_line_vals = move._check_and_allocate_to_virtual_location()
            move.update({"move_line_ids": move_line_vals})

    def _get_grouped_stock_quants(self):
        StockQuant = self.env["stock.quant"]
        quants = StockQuant.search(
            [
                ('product_id', 'in', self.move_ids.product_id.ids),
                ('location_id', 'child_of', self.location_id.ids)
            ],
            order="product_id, location_id, package_id"
        )
        grouped_records = groupby(
            quants,
            key=lambda x: (x.product_id, x.location_id, x.package_id)
        )
        return {key: sum(StockQuant.concat(*quant_groups).mapped('quantity')) \
                for key, quant_groups in grouped_records}

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        def _add_readonly_condition(node):
            readonly_condition = "approval_readonly"
            if node.get("readonly"):
                node.set(
                    "readonly",
                    f"({node.attrib.pop('readonly')}) or {readonly_condition}",
                )

        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == 'form':
            nodes = arch.xpath("//group//field") + arch.xpath("//page[@name='note']//field") + arch.xpath("//field[@name='move_ids_without_package']")
            for node in nodes:
                if node.get("name") in ["approval_readonly"]:
                    continue
                _add_readonly_condition(node)

        return arch, view

    @api.model
    def _get_fields_stock_barcode(self):
        return super()._get_fields_stock_barcode() + ['picking_internal_code']
