from odoo import api, fields, models
from odoo.osv import expression


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    plain_name = fields.Char(readonly=False)

    @api.depends_context('show_plain_name')
    def _compute_display_name(self):
        show_plain_name = self.env.context.get('show_plain_name')
        for rec in self:
            rec.display_name = rec._get_display_name(show_plain_name)

    def _compute_plain_name(self):
        # Not to compute plain_name as origin compute
        for record in self:
            record.plain_name = record.plain_name

    def _get_display_name(self, show_plain_name = False):
        self.ensure_one()
        if show_plain_name:
            return self.plain_name
        else:
            return self.name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = []
        domain = args or []
        # first search by plain name (with =ilike)
        show_plain_name = self.env.context.get('show_plain_name')
        if name and show_plain_name:
            states = self.search(expression.AND([domain, [('plain_name', operator, name)]]), limit=limit)
            result.extend((state.id, state.plain_name) for state in states)
            domain = expression.AND([domain, [('id', 'not in', states.ids)]])
            if limit is not None:
                limit -= len(states)
                if limit <= 0:
                    return result
        # normal search
        result.extend(super().name_search(name, domain, operator, limit))
        return result


class ResCountryDistrict(models.Model):
    _inherit = 'res.country.district'

    plain_name = fields.Char(readonly=False)

    @api.depends_context('show_plain_name')
    def _compute_display_name(self):
        show_plain_name = self.env.context.get('show_plain_name')
        for rec in self:
            rec.display_name = rec._get_display_name(show_plain_name)

    def _compute_plain_name(self):
        # Not to compute plain_name as origin compute
        for record in self:
            record.plain_name = record.plain_name

    def _get_display_name(self, show_plain_name = False):
        self.ensure_one()
        if show_plain_name:
            return self.plain_name
        else:
            return self.name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = []
        domain = args or []
        # first search by plain name (with =ilike)
        show_plain_name = self.env.context.get('show_plain_name')
        if name and show_plain_name:
            districts = self.search(expression.AND([domain, [('plain_name', operator, name)]]), limit=limit)
            result.extend((district.id, district.plain_name) for district in districts)
            domain = expression.AND([domain, [('id', 'not in', districts.ids)]])
            if limit is not None:
                limit -= len(districts)
                if limit <= 0:
                    return result
        # normal search
        result.extend(super().name_search(name, domain, operator, limit))
        return result


class ResCountryWard(models.Model):
    _inherit = 'res.country.ward'

    plain_name = fields.Char(readonly=False)

    @api.depends_context('show_plain_name')
    def _compute_display_name(self):
        show_plain_name = self.env.context.get('show_plain_name')
        for rec in self:
            rec.display_name = rec._get_display_name(show_plain_name)

    def _compute_plain_name(self):
        # Not to compute plain_name as origin compute
        for record in self:
            record.plain_name = record.plain_name

    def _get_display_name(self, show_plain_name = False):
        self.ensure_one()
        if show_plain_name:
            return self.plain_name
        else:
            return self.name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = []
        domain = args or []
        # first search by plain name (with =ilike)
        show_plain_name = self.env.context.get('show_plain_name')
        if name and show_plain_name:
            wards = self.search(expression.AND([domain, [('plain_name', operator, name)]]), limit=limit)
            result.extend((ward.id, ward.plain_name) for ward in wards)
            domain = expression.AND([domain, [('id', 'not in', wards.ids)]])
            if limit is not None:
                limit -= len(wards)
                if limit <= 0:
                    return result
        # normal search
        result.extend(super().name_search(name, domain, operator, limit))
        return result


class ResCountryRegion(models.Model):
    _inherit = 'res.country.region'

    @api.depends_context('show_plain_name')
    def _compute_display_name(self):
        show_plain_name = self.env.context.get('show_plain_name')
        for rec in self:
            rec.display_name = rec._get_display_name(show_plain_name)

    def _get_display_name(self, show_plain_name = False):
        self.ensure_one()
        if show_plain_name:
            return self.plain_name
        else:
            return self.name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = []
        domain = args or []
        # first search by plain name (with =ilike)
        show_plain_name = self.env.context.get('show_plain_name')
        if name and show_plain_name:
            regions = self.search(expression.AND([domain, [('plain_name', operator, name)]]), limit=limit)
            result.extend((region.id, region.plain_name) for region in regions)
            domain = expression.AND([domain, [('id', 'not in', regions.ids)]])
            if limit is not None:
                limit -= len(regions)
                if limit <= 0:
                    return result
        # normal search
        result.extend(super().name_search(name, domain, operator, limit))
        return result
