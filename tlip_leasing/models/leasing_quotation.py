from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LeasingQuotation(models.Model):
    _name = 'leasing.quotation'
    _inherit = ['mail.thread']
    _description = 'Leasing Quotation'

    def _domain_land_plot(self):
        return [
            ('is_land_plot', '=', True),
            ('is_plot_view', '=', False),
            ('internal_usage', '=', False),
            ('state', '=', 'confirm')
        ]

    name = fields.Char('Quotation', required=True,
                       readonly=True, default=lambda self: _('/'))
    active = fields.Boolean(default=True, copy=False)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)
    lessee_id = fields.Many2one('res.partner', 'Lessee', domain=[(
        'customer_code', '!=', False), ('is_blocked', '=', False)])
    lessee_name = fields.Char(
        'Lessee Name', compute='_compute_lessee', store=True, readonly=False)
    lessee_email = fields.Char(
        'Lessee Email', compute='_compute_lessee', store=True, readonly=False)
    lessee_phone = fields.Char(
        'Lessee Phone', compute='_compute_lessee', store=True, readonly=False)
    lessee_payment_email = fields.Char(
        'Email for payment', compute='_compute_lessee', store=True, readonly=False)
    lessee_street = fields.Char(
        compute='_compute_lessee', store=True, readonly=True)
    lessee_street_2 = fields.Char(
        compute='_compute_lessee', store=True, readonly=True)
    lessee_district_id = fields.Many2one('res.country.district', compute='_compute_lessee',
                                         store=True, readonly=True, domain="[('country_state_id', '=?', lessee_state_id)]")
    lessee_ward_id = fields.Many2one('res.country.ward', compute='_compute_lessee',
                                     store=True, readonly=True, domain="[('district_id', '=?', lessee_district_id)]")
    lessee_state_id = fields.Many2one(
        'res.country.state', 'City', compute='_compute_lessee', store=True, readonly=True)
    lessee_country_id = fields.Many2one(
        'res.country', compute='_compute_lessee', store=True, readonly=True)
    land_plot_id = fields.Many2one(
        'stock.location',
        'Land Plot',
        required=True,
        context={'short_name': True},
        domain=_domain_land_plot
    )
    plot_view_id = fields.Many2one(
        'stock.location', 'Plot View', related='land_plot_id.location_id', readonly=True)
    area = fields.Float('Area', digits=(
        16, 2), compute='_compute_land_plot', store=True, readonly=True)
    actual_area = fields.Float('Actual Area', digits=(
        16, 2), compute='_compute_land_plot', store=True, readonly=False)
    land_plot_category_id = fields.Many2one(
        'land.plot.category', related='land_plot_id.land_plot_category_id', readonly=True)
    state = fields.Selection(selection=[
        ('wait', 'Waiting for Client'),
        ('confirm', 'Confirmed'),
        ('expire', 'Expired'),
        ('cancel', 'Cancelled')
    ], default='wait', string='Status')
    issued_date = fields.Date(
        'Issued Date', default=lambda self: fields.Date.context_today(self), required=True)
    due_date = fields.Date('Due Date', required=True)
    note = fields.Text('Note')
    user_id = fields.Many2one(
        'res.users', 'Sales Representative', default=lambda self: self.env.uid)
    attachment_number = fields.Integer(
        'Number of Attachments', compute='_compute_attachment_number')
    agreement_ids = fields.One2many(
        'leasing.agreement',
        'quotation_id',
        string="Reservation Agreement",
        copy=False
    )
    reservation_agreement_count = fields.Integer(
        compute='_compute_agreement_count')
    supplement_agreement_ids = fields.One2many(
        'leasing.supplement',
        'quotation_id',
        string="Supplemental Agreement",
        copy=False
    )
    supplement_agreement_count = fields.Integer(
        compute='_compute_agreement_count')
    termination_agreement_ids = fields.One2many(
        'leasing.termination',
        'quotation_id',
        string="Termination Agreement",
        copy=False
    )
    termination_agreement_count = fields.Integer(
        compute='_compute_agreement_count')

    @api.depends('land_plot_id')
    def _compute_land_plot(self):
        for record in self:
            record.area = record.land_plot_id.saleable_area
            record.actual_area = record.land_plot_id.saleable_area

    @api.depends('lessee_id')
    def _compute_lessee(self):
        for record in self:
            record.lessee_name = record.lessee_id.name
            record.lessee_email = record.lessee_id.email
            record.lessee_phone = record.lessee_id.phone
            record.lessee_payment_email = record.lessee_id.payment_email
            record.lessee_street = record.lessee_id.street
            record.lessee_street_2 = record.lessee_id.street2
            record.lessee_district_id = record.lessee_id.district_id
            record.lessee_ward_id = record.lessee_id.ward_id
            record.lessee_state_id = record.lessee_id.state_id
            record.lessee_country_id = record.lessee_id.country_id

    def _compute_attachment_number(self):
        domain = [('res_model', '=', self._name), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment']._read_group(
            domain, ['res_id'], ['__count'])
        attachment = dict(attachment_data)
        for request in self:
            request.attachment_number = attachment.get(request.id, 0)

    def _compute_agreement_count(self):
        for record in self:
            record.reservation_agreement_count = len(record.agreement_ids.filtered(
                lambda r: r.state != 'cancel' and r.agreement_type == 'reservation'))
            record.supplement_agreement_count = len(
                record.supplement_agreement_ids.filtered(lambda r: r.state != 'cancel'))
            record.termination_agreement_count = len(
                record.termination_agreement_ids.filtered(lambda r: r.state != 'cancel'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'leasing.quotation.sequence') or _('/')
        records = super().create(vals_list)
        return records

    def action_confirm(self):
        self.write({
            'state': 'confirm',
        })

    def action_cancel(self):
        self.write({
            'state': 'cancel',
            'active': False
        })

    @api.model
    def _check_and_expire_quotations(self):
        today = fields.Date.today()
        expired_quotations = self.search([
            ('state', 'not in', ['expire', 'cancel']),
            ('due_date', '<', today)
        ])
        expired_quotations.write({
            'state': 'expire',
        })

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id(
            'base.action_attachment')
        res['domain'] = [('res_model', '=', self._name),
                         ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': self._name,
                          'default_res_id': self.id}
        return res

    def action_get_reservation_agreement_view(self, res_id=None):
        self.ensure_one()
        if not res_id:
            res_id = self.agreement_ids.filtered(
                lambda r: r.state != 'cancel')[:1].id
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.action_reservation_agreement_view')
        action.update({
            'views': [(self.env.ref('tlip_leasing.reservation_agreement_view_form').id, 'form')],
            'target': 'current',
            'res_id': res_id
        })
        return action

    def action_get_supplement_agreement_view(self):
        self.ensure_one()
        if not self.supplement_agreement_ids:
            return False

        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.action_supplemental_agreement_view')
        action.update({
            'domain': [('quotation_id', '=', self.id)],
            'target': 'current',
        })
        return action

    def action_get_termination_agreement_view(self):
        self.ensure_one()
        if not self.termination_agreement_ids:
            return False

        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.action_termination_agreement_view')
        action.update({
            'domain': [('quotation_id', '=', self.id)],
            'target': 'current'
        })
        return action

    def _prepare_reservation_agreement_vals(self):
        self.ensure_one()
        return {
            'quotation_id': self.id,
            'agreement_type': 'reservation',
            'land_plot_id': self.land_plot_id.id,
            'plot_view_id': self.plot_view_id.id,
            'land_plot_category_id': self.land_plot_category_id.id,
            'area': self.area,
            'actual_area': self.actual_area,
            'lessee_id': self.lessee_id.id,
            'lessee_name': self.lessee_name,
            'lessee_email': self.lessee_email,
            'lessee_phone': self.lessee_phone,
            'lessee_street': self.lessee_street,
            'lessee_street_2': self.lessee_street_2,
            'lessee_district_id': self.lessee_district_id.id,
            'lessee_ward_id': self.lessee_ward_id.id,
            'lessee_state_id': self.lessee_state_id.id,
            'lessee_country_id': self.lessee_country_id.id,
        }

    def action_create_reservation_agreement(self):
        self.ensure_one()
        if self.agreement_ids.filtered(lambda r: r.state != 'cancel' and r.agreement_type == 'reservation'):
            raise UserError(
                _("Reservation Agreement has already been created."))

        res_id = self.env['leasing.agreement'].create(
            [self._prepare_reservation_agreement_vals()]).id
        return self.action_get_reservation_agreement_view(res_id)

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)

        if view_type == 'form':
            hidden_btns = arch.xpath("//button")
            for node in hidden_btns:
                # Add condition if not active to all buttons in form view
                archived_condition = "not active"
                if node.get("invisible"):
                    node.set(
                        'invisible', f"{archived_condition} or ({node.attrib.pop('invisible')})")
                else:
                    node.set('invisible', archived_condition)
        return arch, view

    def write(self, vals):
        if any(not rec.active for rec in self) and not (self.env.su or self.env.context.get("allow_update_archived")):
            raise UserError(
                _("Do not allow to update on archived Leasing Quotation"))
        return super().write(vals)
