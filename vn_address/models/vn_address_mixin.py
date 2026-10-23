from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VnAddressMixin(models.AbstractModel):
    _name = "vn.address.mixin"
    _description = "Vn Address Mixin"

    ward_id = fields.Many2one(
        'res.country.ward', tracking=True, domain="[('district_id', '=?', district_id)]")
    district_id = fields.Many2one(
        'res.country.district', tracking=True, domain="[('country_state_id', '=?', state_id)]")
    region_id = fields.Many2one(
        'res.country.region', tracking=True, domain="[('country_id', '=?', country_id)]")
    state_id = fields.Many2one(
        'res.country.state', tracking=True, domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country', tracking=True)
    zip = fields.Char()

    @api.onchange('ward_id')
    def onchange_ward(self):
        if self.ward_id:
            self.district_id = self.ward_id.district_id
            self.state_id = self.district_id.country_state_id
            self.region_id = self.state_id.region_id
            self.country_id = self.state_id.country_id

    @api.onchange('district_id')
    def onchange_district(self):
        ward_domain = []
        if self.district_id:
            if self.ward_id and self.ward_id.id not in self.district_id.ward_ids.ids:
                self.ward_id = False
            ward_domain = [('district_id', '=', self.district_id.id)]
            self.state_id = self.district_id.country_state_id
            self.region_id = self.state_id.region_id
            self.country_id = self.state_id.country_id
        return {
            'domain': {
                'ward_id': ward_domain
            }
        }
    
    @api.onchange('state_id')
    def onchange_state(self):
        ward_domain = []
        district_domain = []
        if self.state_id:
            if self.district_id and self.district_id.id not in self.state_id.district_ids.ids:
                self.district_id = False
            if self.ward_id and self.ward_id.id not in self.district_id.ward_ids.ids:
                self.ward_id = False
            self.country_id = self.state_id.country_id
            self.region_id = self.state_id.region_id
            district_domain = [('country_state_id', '=', self.state_id.id)]
            ward_domain = [('district_id', 'in', self.state_id.district_ids.ids)]
        return {
            'domain': {
                'ward_id': ward_domain,
                'district_id': district_domain
            }
        }

    @api.onchange('country_id')
    def onchange_country(self):
        ward_domain = []
        district_domain = []
        state_domain = []
        region_domain = []
        if self.country_id:
            if self.region_id and self.region_id.id not in self.country_id.region_ids.ids:
                self.region_id = False
            if self.state_id and self.state_id.id not in self.country_id.state_ids.ids:
                self.state_id = False
            if self.district_id and self.district_id.id not in self.state_id.district_ids.ids:
                self.district_id = False
            if self.ward_id and self.ward_id.id not in self.district_id.ward_ids.ids:
                self.ward_id = False
            region_domain = [('country_id', '=', self.country_id.id)]
            state_domain = [('country_id', '=', self.country_id.id)]
            district_domain = [('country_state_id', '=', self.state_id.id)]
            ward_domain = [('district_id', 'in', self.state_id.district_ids.ids)]
        return {
            'domain': {
                'ward_id': ward_domain,
                'district_id': district_domain,
                'state_id': state_domain,
                'region_id': region_domain
            }
        }

    api.model
    def _valid_field_parameter(self, field, name):
        if name == 'tracking':
            return True
        return super(VnAddressMixin, self)._valid_field_parameter(field, name)
