import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LandPlot(models.Model):
    _name = "stock.location"
    _inherit = ["stock.location", "approval.matrix.mixin",
                "mail.thread", "mail.activity.mixin"]
    _description = 'Land Plot'

    usage = fields.Selection(compute='_compute_usage', store=True, readonly=False)
    land_plot_category_id = fields.Many2one(
        'land.plot.category', 'Land Plot Category', compute="_compute_land_plot_category_id", store=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('wait_for_approval', 'Waiting for Approval'),
        ('confirm', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    lease_state = fields.Selection(selection=[
        ('vacant', 'Vacant'),
        ('under_negotiation', 'Under Negotiation'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied')
    ], default='vacant', string='Lease Status')
    internal_usage = fields.Boolean('Internal Usage', default=False)
    lease_usage = fields.Boolean('Lease Usage', default=False)
    is_plot_view = fields.Boolean('Plot View', default=False)
    gross_area = fields.Float('Gross Area (m2)')
    saleable_area = fields.Float('Saleable Area (m2)', compute='_compute_saleable_area',
                                 recursive=True, store=True)
    occupied_area = fields.Float(
        'Occupied Area (m2)', compute='_compute_occupied_area', recursive=True)
    reserved_area = fields.Float(
        'Reserved Area (m2)', compute='_compute_reserved_area', recursive=True)
    vacant_area = fields.Float(
        'Vacant Area (m2)', compute='_compute_vacant_area', recursive=True)
    internal_usage_area = fields.Float(
        'Internal Usage Area (m2)', compute='_compute_internal_usage_area', recursive=True)
    latitute = fields.Float('Latitude')
    longitude = fields.Float('Longitude')
    date_start = fields.Date('Effective From')
    date_end = fields.Date('Effective To')
    layout_data = fields.Text(copy=False)
    tooltip_data = fields.Text('Tooltip Data', compute='_compute_tooltip_data')
    layout_image = fields.Image('Layout Map', attachment=True, copy=False)
    layout_image_url = fields.Char(
        'Layout URL', compute='_compute_layout_image_url')
    has_layout = fields.Boolean(compute='_compute_has_layout')
    is_land_plot = fields.Boolean()
    land_plot_group_id = fields.Many2one('land.plot.group', string='Group')
    map_location = fields.Char('Location')
    footprint_area = fields.Float('Footprint Area')
    floor_area = fields.Float('Floor Area')
    security_house = fields.Char('Security House')
    pump_house = fields.Char('Pump House')
    coordinate_ids = fields.One2many('plot.coordinate', 'land_plot_id')
    damage_location = fields.Boolean(string="Is a Damage Location")
    maintenance_location = fields.Boolean(string="Is a Maintenance Location")
    is_exported_for_use = fields.Boolean(string="Is Issuance for Use", default=False)

    @api.constrains("gross_area", "saleable_area", "is_plot_view")
    def _check_saleable_area(self):
        for rec in self:
            if rec.gross_area < 0:
                raise UserError(
                    _(f"({rec.display_name}) Gross area value must be positive."))

            if rec.saleable_area < 0:
                raise UserError(
                    _(f"({rec.display_name}) Saleable area value must be positive."))

            if rec.saleable_area > rec.gross_area and not rec.is_plot_view:
                raise UserError(
                    _(f"({rec.display_name}) Saleable area must be smaller or equal to gross area."))

    @api.constrains("name", "location_id", "company_id", "is_plot_view")
    def _check_unique_location_name(self):
        for record in self:
            if not record.name:
                continue
            duplicate_location_counts = record.search_count(
                [
                    ("id", "!=", record.id),
                    ("name", "=", record.name),
                    ("location_id", "=", record.location_id.id),
                    ("company_id", "=", record.company_id.id),
                    ("is_plot_view", "=", record.is_plot_view),
                ]
            )
            if duplicate_location_counts > 0:
                raise UserError(
                    _(f"Plot view '{record.name}' already existed. Please select another name"))

    @api.depends('name', 'location_id.complete_name', 'usage')
    @api.depends_context('short_name')
    def _compute_complete_name(self):
        for location in self:
            if 'short_name' in self.env.context:
                location.complete_name = location.name
            else:
                if location.location_id and location.usage != 'view':
                    location.complete_name = '%s/%s' % (
                        location.location_id.complete_name, location.name)
                else:
                    location.complete_name = location.name

    @api.depends(lambda self: (self._rec_name,) if self._rec_name else ())
    @api.depends_context('short_name')
    def _compute_display_name(self):
        if 'short_name' in self.env.context:
            for record in self:
                record.display_name = record.name
        else:
            super()._compute_display_name()

    def _compute_has_layout(self):
        for record in self:
            record.has_layout = True if record.layout_image else False

    @api.depends('is_plot_view', 'child_ids')
    def _compute_usage(self):
        for record in self:
            if record.is_plot_view:
                record.usage = 'view' if record.child_ids else 'internal'

    @api.depends('child_ids.saleable_area')
    def _compute_saleable_area(self):
        for record in self:
            if record.is_plot_view:
                saleable_area = sum(record.child_ids.filtered(
                    lambda rec: rec.state != 'cancel').mapped('saleable_area'))
            else:
                saleable_area = record.saleable_area
            record.saleable_area = saleable_area

    @api.depends('child_ids.lease_state', 'child_ids.saleable_area')
    def _compute_occupied_area(self):
        for record in self:
            record.occupied_area = record._compute_area_with_lease_state(
                'occupied')

    @api.depends('child_ids.lease_state', 'child_ids.saleable_area')
    def _compute_reserved_area(self):
        for record in self:
            record.reserved_area = record._compute_area_with_lease_state(
                'reserved')

    @api.depends('child_ids.lease_state', 'child_ids.saleable_area')
    def _compute_vacant_area(self):
        for record in self:
            record.vacant_area = record._compute_area_with_lease_state(
                'occupied')

    @api.depends('child_ids.internal_usage', 'child_ids.saleable_area')
    def _compute_internal_usage_area(self):
        for record in self:
            internal_locations = record.child_ids.filtered(
                lambda r: r.internal_usage)
            record.internal_usage_area = sum(
                internal_locations.mapped('saleable_area'))

    def _compute_tooltip_data(self):
        for record in self:
            tooltip_data = record._prepare_tooltip_data()
            record.tooltip_data = json.dumps(
                tooltip_data) if tooltip_data else None

    def _compute_layout_image_url(self):
        for record in self:
            if record.is_plot_view:
                record.layout_image_url = f'/web/image?model={self._name}&id={record.id}&field=layout_image'
            else:
                record.layout_image_url = None

    def _compute_area_with_lease_state(self, lease_state):
        self.ensure_one()
        locations = self.child_ids.filtered(
            lambda r: r.lease_state == lease_state)
        return sum(locations.mapped('saleable_area'))

    @api.depends('location_id')
    def _compute_land_plot_category_id(self):
        for record in self:
            land_plot_category = record.land_plot_category_id
            if record.location_id:
                land_plot_category = record.location_id.land_plot_category_id
            record.land_plot_category_id = land_plot_category

    def _prepare_tooltip_data(self):
        self.ensure_one()
        if not self.is_plot_view:
            return None

        data = []
        for child in self.child_ids:
            data.append({
                'location_id': child.id,
                'location_name': child.name,
                'lease_state': dict(self._fields['lease_state'].selection).get(child.lease_state)
            })
        return data

    def write(self, vals):
        if 'layout_data' in vals:
            vals.update({
                'layout_data': json.dumps(vals['layout_data'], indent=4, separators=(',', ': '))
            })
        return super().write(vals)

    def action_open_layout(self):
        self.ensure_one()
        if not self.layout_image:
            raise UserError(
                _('There is no land plot or no layout map available. Please check and try again.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Layout'),
            'res_id': self.id,
            'res_model': self._name,
            'view_type': 'plan',
            'view_mode': 'plan',
            'views': [(self.env.ref('tlip_stock.view_plan_map').id, 'plan')],
            'target': 'current',
            'context': dict(self.env.context) or {}
        }

    def action_open_child_plots(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            'tlip_stock.action_land_plot_view')
        action['domain'] = [('location_id', 'child_of', self.id),
                            ('is_plot_view', '=', False)]
        action['context'] = {
            'default_is_plot_view': False,
            'default_usage': 'internal',
            'default_location_id': self.id
        }
        return action

    def action_submit_approval(self):
        if self.filtered(lambda r: r.state != 'draft'):
            raise UserError(
                _('You cannot submit a land plot view that is not in Draft state.'))
        self._validate_approval()
        action = super().action_submit_approval()
        action['context']['default_name'] = _(
            f'Approval Plan Plot {self.complete_name}')
        return action

    def action_confirm(self):
        self.state = 'confirm'

    def action_reset(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'

    def _trigger_action_approve(self):
        self.write({'state': 'confirm'})

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval',
        })
        return result

    def _trigger_action_withdraw(self, reason: str):
        self.action_cancel()
        super()._trigger_action_withdraw(reason)

    def _validate_approval(self):
        for rec in self:
            if rec.saleable_area > rec.gross_area:
                raise UserError(
                    _(f"({rec.display_name}) Saleable area must be smaller or equal to gross area."))
