from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'vn.address.mixin']
    _rec_names_search = ['name', 'customer_code', 'vendor_code', 'vat', 'short_name']

    short_name = fields.Char(string='Short Name')
    epe_non_epe = fields.Selection(
        [('epe', 'EPE'),
         ('no_epe', 'Non-EPE')],
        required=True, string='EPE/Non-EPE', default='epe',
        tracking=True)
    fax = fields.Char('Fax')
    payment_email = fields.Char('Payment Email')
    customer_code = fields.Char()
    customer_state = fields.Selection([
        ("draft", "Draft"),
        ("to_approve", "Waiting for Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected")], string="Status", default="draft")
    vendor_code = fields.Char()
    vendor_state = fields.Selection([
        ("draft", "Draft"),
        ("to_approve", "Waiting for Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected")], string="Status", default="draft")
    internal_approval_state = fields.Boolean(help="Allow to select this partner in some modules (payment, purchase, etc.)")

    name_en = fields.Char(string='Name (EN)')
    vendor_type_ids = fields.Many2many(
        comodel_name='res.partner.type',
        relation="partner_vendor_type_rel",
        column1="type_id",
        column2="vendor_id",
        string="Type of Vendor"
    )
    customer_type_ids = fields.Many2many(
        comodel_name='res.partner.type',
        relation="partner_customer_type_rel",
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

    attachment_number = fields.Integer(
        'Number of Attachments', compute='_compute_attachment_number')
    cr_ids = fields.One2many(
        "res.partner.cr", "reference_partner_id", string="Updated Info Change Request")
    last_cr_date = fields.Date(
        string="Last Modified Date", compute="_compute_last_cr_date", store=True)
    is_blocked = fields.Boolean(string="Blocked", default=False)
    customer_registration_date = fields.Date(
        string="Customer Registration Date")
    vendor_registration_date = fields.Date(string="Vendor Registration Date")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def _get_exclude_partner_ids(self):
        """Return a clean list of partner IDs to exclude from uniqueness checks."""
        self.ensure_one()
        ids = (
            [self.id]
        ) + (
            [self.parent_id.id] if self.parent_id else []
        ) + (
            [child.id for child in self.child_ids] if self.child_ids else []
        )
        return list(filter(bool, ids))

    @api.constrains("vat", "country_id")
    def _constrains_vat(self):
        for record in self:
            if not (record.vat and record.country_id):
                continue
            existing_contacts = record.search(
                [("vat", "=", record.vat), ("country_id", "=", record.country_id.id),
                 ("id", "not in", record._get_exclude_partner_ids())]
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
        for record in self:
            if not (record.id_number and record.country_id):
                continue
            existing_contacts = record.search(
                [("id_number", "=", record.id_number), ("country_id", "=",
                                                        record.country_id.id), ("id", "not in", record._get_exclude_partner_ids())]
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

    def _compute_attachment_number(self):
        domain = [('res_model', '=', 'res.partner'),
                  ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment']._read_group(
            domain, ['res_id'], ['__count'])
        attachment = dict(attachment_data)
        for request in self:
            request.attachment_number = attachment.get(request.id, 0)

    @api.depends("cr_ids", "cr_ids.state", "cr_ids.date_approved")
    def _compute_last_cr_date(self):
        self.mapped("cr_ids")
        for partner in self:
            completed_cr_ids = partner.cr_ids.filtered(
                lambda cr: cr.state == "approved" and cr.date_approved)
            last_cr_date = completed_cr_ids and max(
                completed_cr_ids.mapped("date_approved")) or False
            partner.last_cr_date = last_cr_date

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id(
            'base.action_attachment')
        res['domain'] = [('res_model', '=', 'res.partner'),
                         ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'res.partner',
                          'default_res_id': self.id}
        return res
    
    def _get_full_address_info(self, include_country=True):
        self.ensure_one()
        adress_vn = [self.street2, self.street, self.ward_id.name, self.district_id.name, self.state_id.name]
        adress_en = [self.street2_en, self.street_en, self.ward_en_id.name, self.district_en_id.name, self.state_en_id.name]
        if include_country:
            adress_vn.append(self.country_id.name)
            adress_en.append(self.country_en_id.name)
        return {
            'partner_address_vn': ', '.join(list(filter(bool, adress_vn))),
            'partner_address_en': ', '.join(list(filter(bool, adress_en)))
        }

    def _get_default_bank_account_info(self):
        self.ensure_one()
        bank_account = self.bank_ids[:1]
        return {
            'bank_id': bank_account.bank_id,
            'bank_account_number': bank_account.acc_number,
            'bank_account_holder': bank_account.acc_holder_name,
            'bank_swift_code': bank_account.bank_bic
        }

    def action_update_contact_info(self):
        self.ensure_one()
        if self.cr_ids.filtered(lambda cr: cr.state in ('draft', 'to_approve')):
            raise UserError("There is already ongoing change request")

        partner_cr_vals = self._prepare_partner_cr_vals()
        self.env["res.partner.cr"].create(partner_cr_vals)

    def _fields_to_change_request(self):
        return [
            'name', 'complete_name', 'title', 'parent_id', 'ref',
            'lang', 'user_id', 'vat', 'bank_ids', 'website', 'comment',
            'category_id', 'employee', 'function', 'type', 'street',
            'street2', 'zip', 'city', 'state_id', 'country_id',
            'partner_latitude', 'partner_longitude', 'email', 'phone',
            'mobile', 'industry_id', 'company_type',
            'company_id', 'color', 'user_ids', 'company_name', 'barcode',
            'name_en', 'vendor_code', 'vendor_type_ids', 'legal_representative_name_vn',
            'legal_representative_title_vn', 'legal_representative_name_en',
            'legal_representative_title_en', 'street_en', 'street2_en',
            'zip_en', 'city_en', 'state_en_id', 'country_en_id', 'country_code_en',
            'parent_company_nationality_id', 'parent_company_client_id',
            'related_company_check', 'emp_fam_related_company', 'id_number',
            'fs_annual_sales', 'fs_annual_pat', 'fs_total_assets',
            'compliance_letter_submission',
            'notarized_bank_act_detail', 'is_company', 'commercial_company_name',
            'district_id', 'ward_id', 'district_en_id', 'ward_en_id',
            'customer_code', 'customer_type_ids', 'short_name'
        ]

    def _validate_action_block(self):
        contracts_count = self.env["purchase.requisition"].search_count(
            [('vendor_id', 'in', self.ids), ('state', 'in', ('draft', 'confirmed'))])
        if contracts_count > 0:
            raise ValidationError(_(
                "The operation cannot be completed: this partner is used in a valid contract(s).\n\n"
                "Please ensure that all contracts have expired or been completed before blocking."
            ))

    def action_block(self):
        self._validate_action_block()
        self.write({"is_blocked": True})

    def action_unblock(self):
        self.write({"is_blocked": False})

    def get_latest_purchase_order(self):
        self.ensure_one()
        return self.env["purchase.order"].search([("partner_id", '=', self.id),
                                                  ('state', 'in', ('purchase', 'done'))],
                                                 order="date_approve desc", limit=1)

    def _message_log(self, **kwargs):
        # OVERRIDE _message_log to skip null record
        if not self:
            return
        super()._message_log(**kwargs)

    def _prepare_partner_cr_vals(self):
        CRMixin = self.env["cr.mixin"]
        cr_fields = self._fields_to_change_request()

        partner_cr_vals = {"reference_partner_id": self.id}
        for name, field in self.env["res.partner.cr"]._fields.items():
            if name in cr_fields:
                partner_cr_vals[name] = CRMixin.convert_value_to_updated_val(
                    field, self[name])

        return partner_cr_vals

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        def _add_readonly_condition(node):
            if node.get("name") in ['vendor_code', 'customer_code', 'customer_type_ids', 'vendor_type_ids']:
                return True
            readonly_condition = "context.get('partner_readonly', False)"
            if node.get("readonly"):
                node.set(
                    "readonly",
                    f"{readonly_condition} or ({node.attrib.pop('readonly')})",
                )
            else:
                node.set("readonly", readonly_condition)

        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            nodes = arch.xpath("//group//field") + arch.xpath("//field") + arch.xpath(
                "//field[@name='child_ids']") + arch.xpath("//field[@name='bank_ids']")
            for node in nodes:
                _add_readonly_condition(node)

        return arch, view
