from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class LeasingAgreement(models.AbstractModel):
    _name = 'leasing.agreement.base'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'approval.matrix.mixin']
    _description = 'Leasing Agreement Base'

    def _domain_land_plot(self):
        return [
            ('is_land_plot', '=', True),
            ('is_plot_view', '=', False),
            ('internal_usage', '=', False),
            ('state', '=', 'confirm')
        ]

    name = fields.Char('Name', required=True, readonly=True,
                       default=lambda self: _('/'), copy=False)
    active = fields.Boolean(default=True, copy=False)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('wait_for_approval', 'Waiting for Approval'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('complete', 'Completed'),
        ('cancel', 'Cancelled')
    ], default='draft')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)
    quotation_id = fields.Many2one('leasing.quotation', copy=False)
    quotation_issued_date = fields.Date(
        related='quotation_id.issued_date', string='Quotation Issued Date', readonly=True)
    issued_date = fields.Date(
        'Issued Date', default=lambda self: fields.Date.context_today(self), required=True)
    lessor_id = fields.Many2one('res.partner', 'Lessor', default=lambda self: self.env.company.partner_id, domain=[
                                ('customer_code', '!=', False), ('is_blocked', '=', False)])
    lessor_street = fields.Char(
        compute='_compute_lessor', store=True, readonly=True)
    lessor_street_2 = fields.Char(
        compute='_compute_lessor', store=True, readonly=True)
    lessor_district_id = fields.Many2one('res.country.district', compute='_compute_lessor',
                                         store=True, readonly=True, domain="[('country_state_id', '=?', lessor_state_id)]")
    lessor_ward_id = fields.Many2one('res.country.ward', compute='_compute_lessor',
                                     store=True, readonly=True, domain="[('district_id', '=?', lessor_district_id)]")
    lessor_state_id = fields.Many2one(
        'res.country.state', 'City', compute='_compute_lessor', store=True, readonly=True)
    lessor_country_id = fields.Many2one(
        'res.country', compute='_compute_lessor', store=True, readonly=True)
    lessee_id = fields.Many2one('res.partner', 'Lessee', domain=[(
        'customer_code', '!=', False), ('is_blocked', '=', False)])
    lessee_name = fields.Char(
        'Lessee Name', compute='_compute_lessee', store=True, readonly=False)
    lessee_email = fields.Char(
        'Lessee Email', compute='_compute_lessee', store=True, readonly=False)
    lessee_phone = fields.Char(
        'Lessee Phone', compute='_compute_lessee', store=True, readonly=False)
    lessee_legal_partner_id = fields.Many2one('res.partner', 'Legal Representative', domain=[
                                              ('customer_code', '!=', False), ('is_blocked', '=', False)])
    lessee_title_id = fields.Many2one(
        'res.partner.title', 'Title', compute='_compute_lessee', store=True, readonly=False)
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
        'stock.location', compute='_compute_land_plot', store=True, readonly=False)
    land_plot_category_id = fields.Many2one(
        'land.plot.category', compute='_compute_land_plot', store=True, readonly=False)
    area = fields.Float('Area', digits=(
        16, 2), compute='_compute_land_plot', store=True, readonly=True)
    actual_area = fields.Float('Actual Area', digits=(
        16, 2), compute='_compute_land_plot', store=True, readonly=False)
    note = fields.Text('Note')
    user_id = fields.Many2one(
        'res.users', related='quotation_id.user_id', readonly=True)
    attachment_number = fields.Integer(
        'Number of Attachments', compute='_compute_attachment_number')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    rental_fee = fields.Float('Rental Fee')
    rental_fee_unit = fields.Selection(selection=[
        ('m2_month', '$/m2/month'),
        ('m2', '$/m2'),
    ], default='m2_month', string='Rental Fee (UoM)')
    reservation_deposit = fields.Float('Reservation Deposit')
    reservation_deposit_type = fields.Selection(selection=[
        ('fixed', 'Fixed price'),
        ('percentage', '%'),
        ('month', 'Month')
    ], default='percentage')
    reservation_deposit_amount = fields.Monetary(
        'Reservation Deposit Amount', compute='_compute_deposit')
    exchange_rate_amount = fields.Monetary('Exchange Rate')
    payment_state = fields.Selection(selection=[
        ('new', 'New'),
        ('wait', 'Waiting for Payment'),
        ('partial', 'Partial Paid'),
        ('paid', 'Paid')
    ], default='new')
    commence_date = fields.Date('Commence Date')
    commence_time = fields.Float('Commence Time')
    expiry_date = fields.Date('Expriry Date')
    expiry_time = fields.Float('Expiry Time')
    investment_certificate_no = fields.Char(
        'Investment Registration Certification No.')
    investment_certificate_date = fields.Date('Investment Registration Date')
    enterprise_certificate_no = fields.Char(
        'Enterprise Registration Certification No.')
    enterprise_certificate_date = fields.Date('Enterprise Registration Date')
    standard_factory_no = fields.Char('Standard Factory No.')
    standard_factory_date = fields.Char('Standard Factory Date')
    map_no = fields.Char('Map No.')
    land_rights_no = fields.Char('Certi of Land Use Rights No.')
    land_rights_restriction = fields.Char(
        'Restriction on Land Use Rights (if any)')
    other_detail = fields.Char('Other details')
    private_use_area = fields.Float('Private Use Area')
    common_use_area = fields.Float('Common Use Area')
    land_use_term = fields.Char('Land Use Term')
    usage_capacity = fields.Float('Usage Capacity')
    number_of_spot = fields.Integer('Number of spot')
    using_purpose = fields.Char('Using Purpose')
    lease_term_year = fields.Integer('Term Years')
    lease_term_month = fields.Integer('Term Months')
    max_industrial_water = fields.Float('Maximum Industrial Water')
    max_electricity = fields.Float('Maximum Electricity Qty')
    payment_frequency = fields.Selection(selection=[
        ('month', 'Monthly / Hàng tháng'),
        ('year', 'Yearly / Hàng năm'),
        ('quarter', 'Quarterly / Hàng quý'),
        ('package', 'Package / Theo gói')
    ])
    payment_term = fields.Integer('Payment Term')
    area_tolerance_within = fields.Float('Area Tolerance Within')
    area_tolerance_exceed = fields.Float('Area Tolerance Exceeded')
    price_adjusted = fields.Float('Price Adjust')
    construction_date_from = fields.Date('Construction Date From')
    construction_date_to = fields.Date('Construction Date To')
    installation_date_from = fields.Date('Installation Date From')
    installation_date_to = fields.Date('Installation Date To')
    trial_production_date_from = fields.Date('Trial Production Date From')
    trial_production_date_to = fields.Date('Trial Production Date To')
    official_production_date = fields.Date('Official Production Date')
    lessor_legal_id = fields.Many2one(
        'res.partner', 'Lessor Legal Reprentative')
    lessor_legal_title_id = fields.Many2one(
        'res.partner.title', compute='_compute_lessor_legal', store=True, readonly=False)
    lessor_legal_email = fields.Char(
        compute='_compute_lessor_legal', store=True, readonly=False)
    lessor_legal_fax = fields.Char(
        compute='_compute_lessor_legal', store=True, readonly=False)
    lessor_legal_phone = fields.Char(
        compute='_compute_lessor_legal', store=True, readonly=False)
    lessor_legal_vat = fields.Char(
        compute='_compute_lessor_legal', store=True, readonly=False)
    lessor_legal_account_number = fields.Char()
    lessor_legal_bank_id = fields.Many2one('res.bank')
    lessee_legal_id = fields.Many2one(
        'res.partner', 'Lessee Legal Reprentative')
    lessee_legal_title_id = fields.Many2one(
        'res.partner.title', compute='_compute_lessee_legal', store=True, readonly=False)
    lessee_legal_email = fields.Char(
        compute='_compute_lessee_legal', store=True, readonly=False)
    lessee_legal_fax = fields.Char(
        compute='_compute_lessee_legal', store=True, readonly=False)
    lessee_legal_phone = fields.Char(
        compute='_compute_lessee_legal', store=True, readonly=False)
    lessee_legal_vat = fields.Char(
        compute='_compute_lessee_legal', store=True, readonly=False)
    lessee_legal_account_number = fields.Char()
    lessee_legal_bank_id = fields.Many2one('res.bank')
    handover_date = fields.Date('Handover Date')
    using_time = fields.Selection([
        ('24h', '24h'),
        ('working_day', 'Working Day')
    ], string='Time of using the Parking Spot')
    revenue_sharing_ratio = fields.Float('Revenue Sharing Ratio (%)')
    adjusted_fee_amount = fields.Monetary('Adjusted Price')
    is_hardcopy_upload = fields.Boolean(default=False)
    automatic_tariff_generation = fields.Boolean('Automatic Tariff Generation')
    tariff_generation_frequency = fields.Selection(
        [('based_on_tlip', 'Based on TLIP'), ('custom', 'Custom')],
        'Tariff Generation Frequency')

    @api.depends('lessor_id')
    def _compute_lessor(self):
        for record in self:
            record.lessor_street = record.lessor_id.street
            record.lessor_street_2 = record.lessor_id.street2
            record.lessor_district_id = record.lessor_id.district_id
            record.lessor_ward_id = record.lessor_id.ward_id
            record.lessor_state_id = record.lessor_id.state_id
            record.lessor_country_id = record.lessor_id.country_id

    @api.depends('lessee_id')
    def _compute_lessee(self):
        for record in self:
            record.lessee_name = record.lessee_id.name
            record.lessee_email = record.lessee_id.email
            record.lessee_phone = record.lessee_id.phone
            record.lessee_street = record.lessee_id.street
            record.lessee_street_2 = record.lessee_id.street2
            record.lessee_district_id = record.lessee_id.district_id
            record.lessee_ward_id = record.lessee_id.ward_id
            record.lessee_state_id = record.lessee_id.state_id
            record.lessee_country_id = record.lessee_id.country_id
            record.lessee_title_id = record.lessee_id.title

    @api.depends('land_plot_id')
    def _compute_land_plot(self):
        for record in self:
            record.plot_view_id = record.land_plot_id.location_id
            record.land_plot_category_id = record.land_plot_id.land_plot_category_id
            record.area = record.land_plot_id.saleable_area
            record.actual_area = record.land_plot_id.saleable_area

    @api.depends('rental_fee_ids', 'rental_fee_ids.amount')
    def _compute_fee_amount(self):
        for record in self:
            record.total_fee_amount = sum(
                record.rental_fee_ids.mapped('amount'))

    @api.depends('lessor_legal_id')
    def _compute_lessor_legal(self):
        for record in self:
            record.lessor_legal_title_id = record.lessor_legal_id.title
            record.lessor_legal_email = record.lessor_legal_id.email
            record.lessor_legal_fax = record.lessor_legal_id.fax
            record.lessor_legal_phone = record.lessor_legal_id.phone
            record.lessor_legal_vat = record.lessor_legal_id.vat

    @api.depends('lessee_legal_id')
    def _compute_lessee_legal(self):
        for record in self:
            record.lessee_legal_title_id = record.lessee_legal_id.title
            record.lessee_legal_email = record.lessee_legal_id.email
            record.lessee_legal_fax = record.lessee_legal_id.fax
            record.lessee_legal_phone = record.lessee_legal_id.phone
            record.lessee_legal_vat = record.lessee_legal_id.vat

    def _compute_attachment_number(self):
        domain = [('res_model', '=', self._name), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment']._read_group(
            domain, ['res_id'], ['__count'])
        attachment = dict(attachment_data)
        for record in self:
            record.attachment_number = attachment.get(record.id, 0)

    @api.depends('area', 'actual_area', 'rental_fee', 'reservation_deposit_type', 'exchange_rate_amount', 'reservation_deposit')
    def _compute_deposit(self):
        for record in self:
            area = record.actual_area or record.area
            if record.reservation_deposit_type == 'percentage':
                record.reservation_deposit_amount = record.rental_fee * area * \
                    (record.reservation_deposit / 100) * \
                    record.exchange_rate_amount
            elif record.reservation_deposit_type == 'month':
                record.reservation_deposit_amount = record.rental_fee * area * \
                    record.reservation_deposit * record.exchange_rate_amount
            else:
                record.reservation_deposit_amount = record.reservation_deposit

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id(
            'base.action_attachment')
        res['domain'] = [('res_model', '=', self._name),
                         ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': self._name,
                          'default_res_id': self.id}
        return res

    def action_submit_approval(self):
        action = super().action_submit_approval()
        action['context']['default_name'] = _(
            f'Approval {self._description} {self.name}')
        return action

    def _trigger_action_after_submit(self, request):
        res = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval'
        })
        return res

    def _trigger_action_approve(self):
        self.write({'state': 'approve'})

    def _trigger_action_refuse(self):
        self.write({'state': 'reject'})

    def action_cancel(self):
        self.write({'state': 'cancel'})
        if self.approval_request_id and self.approval_request_id.request_status in ('new', 'pending'):
            self.approval_request_id.action_cancel()

    def action_complete(self):
        self.write({'state': 'complete'})

    def action_reject_document(self):
        self.write({
            'state': 'reject'
        })

    def action_get_quotation_view(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.action_leasing_quotation_view')
        action.update({
            'views': [(self.env.ref('tlip_leasing.leasing_quotation_view_form').id, 'form')],
            'target': 'current',
            'res_id': self.quotation_id.id,
        })
        return action

    def action_print(self):
        self.ensure_one()
        ir_model = self.env['ir.model'].search([('model', '=', self._name)])
        docx_template = self.env['docx.template'].search([
            ('model_id', '=', ir_model.id)
        ], limit=1)
        if not docx_template:
            return

        ctx = {
            'menu_action_id': docx_template.id,
            'active_ids': self.ids,
            'active_model': self._name
        }
        return self.env['docx.template'].with_context(**ctx).make_docx_pdf_report()

    def action_preview(self):
        pass

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        res = super().message_post(**kwargs)
        if kwargs.keys() == {'attachment_ids'}:
            document_ids = kwargs.get('attachment_ids', [])
            if self.env['ir.attachment'].browse(document_ids):
                self.filtered(lambda r: r.state == 'approve').write(
                    {'is_hardcopy_upload': True})

        return res

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)

        if view_type == 'form':
            for node in arch.xpath("//button"):
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
                _(f"Do not allow to update on archived {self._description}"))
        return super().write(vals)

    def _get_data_template(self):
        self.ensure_one()
        return {'name': self.name}
