from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError


@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()


class ResPartnerCR(models.Model):
    _name = 'res.partner.cr'
    _inherit = ['format.address.mixin', 'format.vat.label.mixin',
                'mail.thread', 'mail.activity.mixin', 'cr.mixin', 'vn.address.mixin']
    _description = "Res Partner Change Request"
    _order = "complete_name ASC, id DESC"

    _complete_name_displayed_types = ('invoice', 'delivery', 'other')

    name = fields.Char()
    short_name = fields.Char(string='Short Name')
    cr_type = fields.Selection([('vendor', 'Update Vendor'), ('customer', 'Update Customer')])
    complete_name = fields.Char(compute='_compute_complete_name', store=True)
    title = fields.Many2one('res.partner.title')
    parent_id = fields.Many2one('res.partner', string='Related Company')
    parent_name = fields.Char(related='parent_id.name',
                              readonly=True, string='Parent name')
    ref = fields.Char(string='Reference')
    lang = fields.Selection(_lang_get, string='Language',
                            help="All the emails and documents sent to this contact will be translated in this language.")
    active_lang_count = fields.Integer(compute='_compute_active_lang_count')
    user_id = fields.Many2one('res.users', string="Salesperson")
    vat = fields.Char(string='Tax ID',
                      help="The Tax Identification Number. Values here will be validated based on the country format. You can use '/' to indicate that the partner is not subject to tax.")
    bank_ids = fields.Many2many('res.partner.bank', string='Banks')
    website = fields.Char('Website Link')
    comment = fields.Html(string='Notes')
    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                   column2='category_id', string='Business Type')
    employee = fields.Boolean(
        help="Check this box if this contact is an Employee.")
    function = fields.Char(string='Job Position')
    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('other', 'Other Address'),
         ], string='Address Type',
        default='contact')
    # address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state", string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country')
    country_code = fields.Char(
        related='country_id.code', string="Country Code")
    partner_latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    is_company = fields.Boolean(string='Is a Company', default=False,
                                help="Check if the contact is a company, otherwise it is a person")
    industry_id = fields.Many2one('res.partner.industry', 'Industry')
    # company_type is only an interface field, do not use it in business logic
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'),
                                               ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type')
    company_id = fields.Many2one('res.company', 'Company')
    color = fields.Integer(string='Color Index', default=0)
    user_ids = fields.Many2many(
        'res.users', "partner_cr_users_rel", 'cr_id', 'user_id', string='Users')
    commercial_company_name = fields.Char('Company Name Entity')
    company_name = fields.Char('Company Name')
    barcode = fields.Char(
        help="Use a barcode to identify this contact.", company_dependent=True)

    # New field from tlip_procurement
    name_en = fields.Char(string='Name (EN)')
    customer_code = fields.Char()
    vendor_code = fields.Char()
    vendor_type_ids = fields.Many2many(
        comodel_name='res.partner.type',
        relation="partner_cr_vendor_type_rel",
        column1="type_id",
        column2="vendor_id",
        string="Type of Vendor"
    )
    customer_type_ids = fields.Many2many(
        comodel_name='res.partner.type',
        relation="partner_cr_customer_type_rel",
        column1="type_id",
        column2="customer_id",
        string="Type of Customer"
    )
    legal_representative_name_vn = fields.Char(
        string='Legal Representative Name (VN)')
    legal_representative_title_vn = fields.Char(
        string='Legal Representative Title (VN)')
    legal_representative_name_en = fields.Char(
        string='Legal Representative Name (EN)')
    legal_representative_title_en = fields.Char(
        string='Legal Representative Title (EN)')

    # company info
    parent_company_nationality_id = fields.Many2one(
        comodel_name='res.country',
        string='Parent Company Nationality'
    )
    parent_company_client_id = fields.Many2one(
        comodel_name='res.partner',
        string='Parent Company Client code'
    )
    related_company_check = fields.Selection(
        selection=[
            ('no', 'No'),
            ('affiliated', 'Affiliated'),
            ('investor', 'Investor Related'),
        ],
        string='Related Company Check'
    )
    emp_fam_related_company = fields.Boolean(
        string='Employee & Family related Company')
    id_number = fields.Char(string="ID Number")

    # referral info
    fs_annual_sales = fields.Float()
    fs_annual_pat = fields.Float()
    fs_total_assets = fields.Float()
    compliance_letter_submission = fields.Char(
        string="Compliance Letter Submission")
    notarized_bank_act_detail = fields.Char(
        string="Notarized Bank Account Detail")
    copy_fs_file = fields.Binary(string='Copy FS attachment')
    copy_fs_filename = fields.Char()
    copy_client_file = fields.Binary(string='Copy Client list')
    copy_client_filename = fields.Char()
    site_check_file = fields.Binary(string='Site Check report')
    site_check_filename = fields.Char()
    result_site_check = fields.Char('Result of Site Check')
    other_notes = fields.Char('Other notes')

    reason = fields.Text(string='Reason for change')
    effective_date = fields.Date(string='Effective Date')
    summary_change_ids = fields.One2many(
        'partner.summary.change', 'partner_cr_id', string="Changes")
    reference_partner_id = fields.Many2one("res.partner")
    state = fields.Selection([
        ("draft", "Draft"),
        ("to_approve", "Waiting for Approval"),
        ("approved", "Approved"),
        ('complete', 'Completed'),
        ("rejected", "Rejected"),
        ("cancel", "Cancelled")], string="Status", default="draft", tracking=True)
    date_approved = fields.Date()

    _sql_constraints = [
        ('check_name', "CHECK( (type='contact' AND name IS NOT NULL) or (type!='contact') )",
         'Contacts require a name'),
    ]

    def _get_exclude_partner_ids(self):
        """Return a clean list of partner IDs to exclude from uniqueness checks."""
        self.ensure_one()
        ids = (
            [self.reference_partner_id.id] if self.reference_partner_id else []
        ) + (
            [self.reference_partner_id.parent_id.id] if self.reference_partner_id.parent_id else []
        ) + (
            [child.id for child in self.reference_partner_id.child_ids] if self.reference_partner_id.child_ids else []
        )
        return list(filter(bool, ids))

    @api.constrains('barcode')
    def _check_barcode_unicity(self):
        ResPartner = self.env["res.partner"]
        for partner in self:
            exclude_ids = partner._get_exclude_partner_ids()
            if partner.barcode and ResPartner.search_count([('barcode', '=', partner.barcode), ("id", "not in", exclude_ids)]) > 1:
                raise ValidationError(
                    _('Another partner already has this barcode'))

    @api.constrains("vat", "country_id")
    def _constrains_vat(self):
        ResPartner = self.env["res.partner"]
        for record in self:
            if not (record.vat and record.country_id):
                continue
            exclude_ids = record._get_exclude_partner_ids()
            existing_contacts = ResPartner.search(
                [("vat", "=", record.vat), ("country_id", "=", record.country_id.id),
                 ("id", "not in", exclude_ids)]
            )
            if existing_contacts:
                partners_name = ', '.join(filter(bool, [contact.name or contact.display_name for contact in existing_contacts]))
                raise UserError(
                    _("Tax Code(s), Country already assigned.\n"
                      "- Tax ID '%(vat)s', Country '%(country)s' already assigned to partner(s): %(partners)s") % {
                        'vat': record.vat,
                        'country': record.country_id.name,
                        'partners': partners_name,
                    }
                )

    @api.constrains("id_number", "country_id")
    def _constrains_id_number(self):
        ResPartner = self.env["res.partner"]
        for record in self:
            if not (record.id_number and record.country_id):
                continue
            exclude_ids = record._get_exclude_partner_ids()
            existing_contacts = ResPartner.search(
                [("id_number", "=", record.id_number), ("country_id", "=", record.country_id.id),
                 ("id", "not in", exclude_ids)]
            )
            if existing_contacts:
                partners_name = ', '.join(filter(bool, [contact.name or contact.display_name for contact in existing_contacts]))
                raise UserError(
                    _("ID Number, Country already assigned.\n"
                      "- ID Number '%(id_number)s', Country '%(country)s' already assigned to partner(s): %(partners)s") % {
                        'id_number': record.id_number,
                        'country': record.country_id.name,
                        'partners': partners_name,
                    }
                )

    @api.constrains('effective_date')
    def _constrains_effective_date(self):
        for rec in self.filtered(lambda cr: cr.effective_date):
            cr_ids = rec.reference_partner_id.cr_ids - rec
            if cr_ids.filtered(
                lambda cr, rec=rec: cr.state not in ("complete", "rejected", "cancel") and
                cr.effective_date and
                cr.effective_date == rec.effective_date
            ):
                raise UserError(
                    _("The operation cannot be completed: this change request has an effective date which is duplicated with another"))

    def _get_complete_name(self):
        self.ensure_one()
        displayed_types = self._complete_name_displayed_types
        type_description = dict(
            self._fields['type']._description_selection(self.env))

        name = self.name or ''
        if self.company_name or self.parent_id:
            if not name and self.type in displayed_types:
                name = type_description[self.type]
            if not self.is_company:
                name = f"{self.commercial_company_name or self.sudo().parent_id.name}, {name}"
        return name.strip()

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name', 'commercial_company_name')
    def _compute_complete_name(self):
        for partner in self:
            partner.complete_name = partner.with_context(
                {})._get_complete_name()

    @api.depends('lang')
    def _compute_active_lang_count(self):
        lang_count = len(self.env['res.lang'].get_installed())
        for partner in self:
            partner.active_lang_count = lang_count

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id and self.country_id != self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'person'

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'

    @api.onchange('company_type')
    def onchange_company_type(self):
        self.is_company = (self.company_type == 'company')

    @api.model
    def cron_activate_change_request(self):
        today = fields.Date.today()
        effective_cr_ids = self.search(
            [('state', '=', 'approved'), ('effective_date', '<=', today)])
        for cr in effective_cr_ids:
            cr._action_effective()

    def action_cancel(self):
        self.write({"state": "cancel"})

    def _fields_tracking_change(self):
        return [
            'name', 'complete_name', 'title', 'ref',
            'lang', 'user_id', 'vat', 'website', 'comment',
            'category_id', 'employee', 'function', 'type', 'street',
            'street2', 'zip', 'city', 'state_id', 'country_id',
            'partner_latitude', 'partner_longitude', 'email', 'phone',
            'mobile', 'industry_id', 'company_type',
            'color', 'company_name', 'barcode', 'name_en', 'vendor_code', 'vendor_type_ids',
            'legal_representative_name_vn', 'legal_representative_title_vn',
            'legal_representative_name_en', 'legal_representative_title_en', 'street_en',
            'street2_en', 'zip_en', 'city_en', 'state_en_id', 'country_en_id',
            'country_code_en', 'parent_company_nationality_id', 'parent_company_client_id',
            'related_company_check', 'emp_fam_related_company', 'id_number',
            'fs_annual_sales', 'fs_annual_pat', 'fs_total_assets',
            'compliance_letter_submission', 'notarized_bank_act_detail',
            'district_id', 'ward_id', 'district_en_id', 'ward_en_id',
            'copy_fs_filename', 'copy_client_filename', 'site_check_filename',
            'result_site_check', 'other_notes', 'short_name'
        ]

    def _action_effective(self):
        self.ensure_one()
        vals = self._prepare_partner_vals()
        self.reference_partner_id.write(vals)
        self.write({"state": "complete"})

    def _prepare_partner_vals(self):
        updated_vals = {}
        fields_vals = self._fields
        for name in self._fields_tracking_change():
            updated_vals[name] = self.convert_value_to_updated_val(
                fields_vals[name], self[name])

        updated_vals["bank_ids"] = [(6, 0, self.bank_ids.ids)]
        return updated_vals

    def _get_difference_record_changes(self, current_record):
        summary_change_vals = super()._get_difference_record_changes(current_record)
        if len(self.bank_ids) > len(current_record.bank_ids):
            new_banks = self.bank_ids - current_record.bank_ids
            summary_change_vals.append(Command.create({
                'name': self._fields["bank_ids"].string,
                'new_value': f"New Bank(s): {', '.join(new_banks.mapped('acc_number'))}"
            }))

        return summary_change_vals

    def write(self, vals):
        if 'bank_ids' in vals:
            ResPartnerBank = self.env["res.partner.bank"]
            for bank_vals in vals.get("bank_ids", []):
                if bank_vals[0] == 3:
                    # Here happens Command.unlink -> (3, bank_id)
                    bank = ResPartnerBank.browse(bank_vals[1])
                    if bank.partner_id:
                        raise UserError(
                            _(f"You cannot remove bank linked with contact: Account Number - {bank.acc_number}"))

        return super().write(vals)
