from odoo import api, models, fields, _


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    internal_code = fields.Selection(
        selection=[
            ('internal', 'Internal'),
            ('dispose', 'Dispose'),
            ('damage', 'Damage'),
            ('maintenance', 'Maintenance'),
            ('inspect', 'Inspect')
        ], compute="_compute_internal_code", store=True, readonly=False
    )
    available_location_dest_ids = fields.Many2many('stock.location', compute="_compute_available_location_dest_ids")
    default_location_dest_id = fields.Many2one(domain="[('id', 'in', available_location_dest_ids)]")

    @api.depends("code")
    def _compute_internal_code(self):
        for rec in self:
            internal_code = False
            if rec.code == "internal":
                internal_code = "internal"

            rec.internal_code = internal_code

    @api.depends("internal_code")
    def _compute_available_location_dest_ids(self):
        StockLocations = self.env['stock.location'].search([])
        for rec in self:
            domain = rec._get_domain_locations_internal_code()
            rec.available_location_dest_ids = StockLocations.filtered_domain(domain)

    @api.onchange("location_id")
    def _onchange_source_location(self):
        self.ensure_one()
        if self.internal_code == "inspect":
            self.default_location_dest_id = self.default_location_src_id

    def _get_domain_locations_internal_code(self):
        self.ensure_one()
        domain = []
        if self.internal_code == "dispose":
            domain.append(('scrap_location', '=', True))
        elif self.internal_code == "damage":
            domain.append(('damage_location', '=', True))
        elif self.internal_code == "maintenance":
            domain.append(('maintenance_location', '=', True))

        return domain
