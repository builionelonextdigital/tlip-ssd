from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VnAddressMixin(models.AbstractModel):
    _inherit = "vn.address.mixin"

    street_en = fields.Char(string="Street (EN)")
    street2_en = fields.Char(string="Street 2 (EN)")
    zip_en = fields.Char(change_default=True, string="Zip (EN)")
    city_en = fields.Char(string="City (EN)")
    ward_en_id = fields.Many2one(
        "res.country.ward",
        domain="[('district_id', '=?', district_en_id)]",
        string="Ward (EN)",
        context={'show_plain_name': True}
    )
    district_en_id = fields.Many2one(
        "res.country.district",
        domain="[('country_state_id', '=?', state_en_id)]",
        string="District (EN)",
        context={'show_plain_name': True}
    )
    region_en_id = fields.Many2one(
        "res.country.region",
        domain="[('country_id', '=?', country_en_id)]",
        string="Region (EN)",
        context={'show_plain_name': True}
    )
    state_en_id = fields.Many2one(
        "res.country.state",
        domain="[('country_id', '=?', country_en_id)]",
        string="State (EN)",
        context={'show_plain_name': True}
    )
    country_en_id = fields.Many2one(
        "res.country",
        string="Country (EN)",
        context={'show_plain_name': True}
    )
    country_code_en = fields.Char(
        related="country_en_id.code", string="Country Code (EN)"
    )

    @api.onchange("ward_en_id")
    def onchange_ward_en(self):
        if self.ward_en_id:
            self.district_en_id = self.ward_en_id.district_id
            self.state_en_id = self.district_en_id.country_state_id
            self.region_en_id = self.state_en_id.region_id
            self.country_en_id = self.state_en_id.country_id

    @api.onchange("district_en_id")
    def onchange_district_en(self):
        ward_domain = []
        if self.district_en_id:
            if (
                self.ward_en_id
                and self.ward_en_id.id not in self.district_en_id.ward_ids.ids
            ):
                self.ward_en_id = False
            ward_domain = [("district_id", "=", self.district_en_id.id)]
            self.state_en_id = self.district_en_id.country_state_id
            self.region_en_id = self.state_en_id.region_id
            self.country_en_id = self.state_en_id.country_id
        return {"domain": {"ward_id": ward_domain}}

    @api.onchange("state_en_id")
    def onchange_state_en(self):
        ward_domain = []
        district_domain = []
        if self.state_en_id:
            if (
                self.district_en_id
                and self.district_en_id.id not in self.state_en_id.district_ids.ids
            ):
                self.district_en_id = False
            if (
                self.ward_en_id
                and self.ward_en_id.id not in self.district_en_id.ward_ids.ids
            ):
                self.ward_en_id = False
            self.country_en_id = self.state_en_id.country_id
            self.region_en_id = self.state_en_id.region_id
            district_domain = [("country_state_en_id", "=", self.state_en_id.id)]
            ward_domain = [("district_en_id", "in", self.state_en_id.district_ids.ids)]
        return {
            "domain": {"ward_en_id": ward_domain, "district_en_id": district_domain}
        }

    @api.onchange("country_en_id")
    def onchange_country_en(self):
        ward_domain = []
        district_domain = []
        state_domain = []
        region_domain = []
        if self.country_en_id:
            if (
                self.region_en_id
                and self.region_en_id.id not in self.country_en_id.region_ids.ids
            ):
                self.region_en_id = False
            if (
                self.state_en_id
                and self.state_en_id.id not in self.country_en_id.state_ids.ids
            ):
                self.state_en_id = False
            if (
                self.district_en_id
                and self.district_en_id.id not in self.state_en_id.district_ids.ids
            ):
                self.district_en_id = False
            if (
                self.ward_en_id
                and self.ward_en_id.id not in self.district_en_id.ward_ids.ids
            ):
                self.ward_en_id = False
            region_domain = [("country_id", "=", self.country_en_id.id)]
            state_domain = [("country_id", "=", self.country_en_id.id)]
            district_domain = [("country_state_id", "=", self.state_en_id.id)]
            ward_domain = [("district_id", "in", self.state_en_id.district_ids.ids)]
        return {
            "domain": {
                "ward_en_id": ward_domain,
                "district_en_id": district_domain,
                "state_en_id": state_domain,
                "region_en_id": region_domain,
            }
        }
