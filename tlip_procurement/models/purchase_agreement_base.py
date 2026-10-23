from odoo import models, fields, api, _
from odoo.tools import format_date
from odoo.exceptions import ValidationError

from ..tools.misc import format_decimal


class PurchaseAgreementBase(models.Model):
    _name = "purchase.agreement.base"
    _inherit = ["mail.thread", "mail.activity.mixin", "approval.matrix.mixin"]
    _description = "Purchase Agreement Base"

    name = fields.Char(
        "Name", required=True, readonly=False, default=lambda self: _("/"), copy=False
    )
    active = fields.Boolean(default=True)
    purchase_contract_type_id = fields.Many2one(
        "purchase.contract.type", "Contract Type"
    )
    contract_type_classification = fields.Selection(
        related="purchase_contract_type_id.classification"
    )
    purpose_en = fields.Char("Purpose (EN)")
    purpose_vn = fields.Char("Purpose (VN)")
    scope_en = fields.Char("Scope of Work (EN)")
    scope_vn = fields.Char("Scope of Work (VN)")
    desc_en = fields.Char("Description (EN)")
    desc_vn = fields.Char("Description (VN)")
    company_id = fields.Many2one('res.company', string='Company')
    buyer_id = fields.Many2one("res.partner", "Buyer", check_company=True, domain="[('is_blocked', '=', False), '|', '|', ('customer_state', '=', 'approved'), ('vendor_state', '=', 'approved'), ('internal_approval_state', '=', True)]")
    buyer_street = fields.Char(compute="_compute_buyer", store=True)
    buyer_street_2 = fields.Char(compute="_compute_buyer", store=True)
    buyer_district = fields.Char(compute="_compute_buyer", store=True)
    buyer_ward = fields.Char(compute="_compute_buyer", store=True)
    buyer_state_id = fields.Many2one(
        "res.country.state",
        string="City",
        compute="_compute_buyer",
        store=True,
    )
    buyer_country_id = fields.Many2one(
        "res.country", compute="_compute_buyer", store=True
    )
    buyer_address_vn = fields.Char("Buyer Address (VN)", compute="_compute_buyer", store=True)
    buyer_address_en = fields.Char("Buyer Address (EN)", compute="_compute_buyer", store=True)
    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        domain="[('vendor_state', '=', 'approved'), ('is_blocked', '=', False), ('company_id', '=', company_id)]",
    )
    vendor_code = fields.Char(compute="_compute_vendor", store=True)
    vendor_street = fields.Char(compute="_compute_vendor", store=True)
    vendor_street_2 = fields.Char(compute="_compute_vendor", store=True)
    vendor_district = fields.Char(compute="_compute_vendor", store=True)
    vendor_ward = fields.Char(compute="_compute_vendor", store=True)
    vendor_state_id = fields.Many2one(
        "res.country.state",
        string="City",
        compute="_compute_vendor",
        store=True,
    )
    vendor_country_id = fields.Many2one(
        "res.country", compute="_compute_vendor", store=True
    )
    vendor_address_vn = fields.Char("Vendor Address (VN)", compute="_compute_vendor", store=True)
    vendor_address_en = fields.Char("Vendor Address (EN)", compute="_compute_vendor", store=True)
    vendor_vat = fields.Char(compute="_compute_vendor", store=True)
    quotation_no = fields.Char("Quotation No.")
    quotation_date = fields.Date("Quotation Date")
    total_amount_untaxed = fields.Float("Total value of contract (untaxed)")
    tax_rate = fields.Float("VAT Rate")
    note = fields.Text("Note")
    commence_date = fields.Date("Commence Date")
    complete_date = fields.Date("Complete Date")
    estimated_month = fields.Float(string="Estimate Time Schedule")
    effective_date_from = fields.Date()
    effective_date_to = fields.Date()
    delivery_time = fields.Integer("Delivery Time")
    delivery_street = fields.Char()
    delivery_street_2 = fields.Char()
    delivery_district_id = fields.Many2one("res.country.district")
    delivery_ward_id = fields.Many2one("res.country.ward")
    delivery_state_id = fields.Many2one("res.country.state")
    delivery_country_id = fields.Many2one("res.country")
    guarantee_period = fields.Integer("Guarantee Period")
    payment_frequency = fields.Selection(
        selection=[
            ('month', 'Monthly / Hàng tháng'),
            ('year', 'Yearly / Hàng năm'),
            ('quarter', 'Quarterly / Hàng quý'),
            ('package', 'Package / Theo gói')
        ],
        default="month",
        string="Payment Frequency",
    )
    payment_term_days = fields.Integer("Payment Term Days")
    payment_term_description = fields.Char("Payment Term Description")
    buyer_legal_name = fields.Char(compute="_compute_buyer", store=True, string="'Buyer Legal Reprentative'", readonly=False)
    buyer_legal_title = fields.Char(compute="_compute_buyer", store=True, readonly=False)
    buyer_legal_attoney_no = fields.Char(compute="_compute_buyer", store=True, readonly=False)
    buyer_legal_email = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_fax = fields.Char(compute="_compute_buyer", store=True, readonly=False)
    buyer_legal_phone = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_vat = fields.Char(compute="_compute_buyer", store=True)
    buyer_legal_beneficiary = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_account_number = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_bank_id = fields.Many2one(
        "res.bank", compute="_compute_buyer", store=True, readonly=False
    )
    vendor_legal_name = fields.Char(string="Vendor Legal Reprentative", compute="_compute_vendor", store=True, readonly=False)
    vendor_legal_title = fields.Char(compute="_compute_vendor", store=True, readonly=False)
    vendor_legal_attoney_no = fields.Char()
    vendor_legal_email = fields.Char(
        compute="_compute_vendor", store=True, readonly=False
    )
    vendor_legal_fax = fields.Char(
        compute="_compute_vendor", store=True, readonly=False
    )
    vendor_legal_phone = fields.Char(
        compute="_compute_vendor", store=True, readonly=False
    )
    vendor_legal_beneficiary = fields.Char(compute="_compute_vendor", store=True, readonly=False)
    vendor_legal_account_number = fields.Char(compute="_compute_vendor", store=True, readonly=False)
    vendor_legal_bank_id = fields.Many2one("res.bank", compute="_compute_vendor", store=True, readonly=False)
    user_id = fields.Many2one("res.users", "Sales Representative")
    attachment_number = fields.Integer(
        "Number of Attachments", compute="_compute_attachment_number"
    )
    currency_id = fields.Many2one("res.currency")
    currency_rate = fields.Float(default=1.0)
    create_date_format = fields.Char(compute="_compute_create_date_format")
    contract_signer_id = fields.Many2one("hr.employee")
    available_hr_job_ids = fields.Many2many(
        "hr.job",
        compute="_compute_available_hr_job_ids",
    )
    amount_in_words_en = fields.Char(compute='_compute_format_amount')
    amount_in_words_vn = fields.Char(compute='_compute_format_amount')
    total_amount_en_text = fields.Char(compute='_compute_format_amount')
    total_amount_vn_text = fields.Char(compute='_compute_format_amount')

    @api.depends("buyer_id", "contract_signer_id")
    def _compute_buyer(self):
        for record in self:
            buyer_field_mapping = {
                "buyer_street": "street",
                "buyer_street_2": "street2",
                "buyer_district": "district_name",
                "buyer_ward": "ward_name",
                "buyer_state_id": "state_id",
                "buyer_country_id": "country_id",
                "buyer_legal_email": "email",
                "buyer_legal_fax": "fax",
                "buyer_legal_phone": "phone",
                "buyer_legal_vat": "vat",
            }
            bank_info_mapping = {
                "buyer_legal_beneficiary": "bank_account_holder",
                "buyer_legal_account_number": "bank_account_number",
                "buyer_legal_bank_id": "bank_id",
            }
            address_info_mapping = {
                "buyer_address_vn": "partner_address_vn",
                "buyer_address_en": "partner_address_en"
            }

            buyer = record.buyer_id
            bank_account_info = buyer._get_default_bank_account_info() if buyer else {}
            partner_address = buyer._get_full_address_info() if buyer else {}

            for field, field_name in buyer_field_mapping.items():
                record[field] = getattr(buyer, field_name)

            for field, field_name in bank_info_mapping.items():
                record[field] = bank_account_info.get(field_name)

            for field, field_name in address_info_mapping.items():
                record[field] = partner_address.get(field_name)

            record.buyer_legal_name = record.contract_signer_id.name
            record.buyer_legal_title = record.contract_signer_id.job_id.name
            record.buyer_legal_attoney_no = record.contract_signer_id.legal_attoney_no

    @api.depends("vendor_id")
    def _compute_vendor(self):
        for record in self:
            field_mapping = {
                "vendor_code": "vendor_code",
                "vendor_street": "street",
                "vendor_street_2": "street2",
                "vendor_district": "district_name",
                "vendor_ward": "ward_name",
                "vendor_state_id": "state_id",
                "vendor_country_id": "country_id",
                "vendor_vat": "vat",
                "vendor_legal_name": "legal_representative_name_vn",
                "vendor_legal_title": "legal_representative_title_vn",
                "vendor_legal_email": "email",
                "vendor_legal_fax": "fax",
                "vendor_legal_phone": "phone",
            }
            bank_info_mapping = {
                "vendor_legal_beneficiary": "bank_account_holder",
                "vendor_legal_account_number": "bank_account_number",
                "vendor_legal_bank_id": "bank_id",
            }
            address_info_mapping = {
                "vendor_address_vn": "partner_address_vn",
                "vendor_address_en": "partner_address_en"
            }
            vendor = record.vendor_id
            bank_account_info = vendor._get_default_bank_account_info() if vendor else {}
            partner_address = vendor._get_full_address_info() if vendor else {}

            for field, field_name in field_mapping.items():
                record[field] = getattr(vendor, field_name)

            for field, field_name in bank_info_mapping.items():
                record[field] = bank_account_info.get(field_name)

            for field, field_name in address_info_mapping.items():
                record[field] = partner_address.get(field_name)

    def _compute_attachment_number(self):
        domain = [("res_model", "=", self._name), ("res_id", "in", self.ids)]
        attachment_data = self.env["ir.attachment"]._read_group(
            domain, ["res_id"], ["__count"]
        )
        attachment = dict(attachment_data)
        for record in self:
            record.attachment_number = attachment.get(record.id, 0)

    def _compute_format_amount(self):
        odoo_env = self.env
        for record in self:
            if record.currency_id:
                record.amount_in_words_en = record.currency_id.with_context(lang='en_US').amount_to_text(
                    record.total_amount_untaxed).capitalize().replace('dong', 'vietnamese dong')
                record.amount_in_words_vn = record.currency_id.with_context(lang='vi_VN').amount_to_text(
                    record.total_amount_untaxed).capitalize().replace('dong', 'đồng')
            else:
                record.amount_in_words_vn = False
                record.amount_in_words_en = False

            record.total_amount_vn_text = format_decimal(
                odoo_env, record.total_amount_untaxed, lang="vi_VN")
            record.total_amount_en_text = format_decimal(
                odoo_env, record.total_amount_untaxed, lang="en_US")

    @api.depends('create_date')
    def _compute_create_date_format(self):
        for record in self:
            record.create_date_format = format_date(self.env, record.create_date) if record.create_date else False

    @api.depends("total_amount_untaxed")
    def _compute_available_hr_job_ids(self):
        min_contract_amount = min(self.mapped("total_amount_untaxed"))
        available_rules = self.env["contract.sign.rule"].get_rules_on_contract_amount(
            min_contract_amount
        )

        for record in self:
            filtered_rules = available_rules.filtered_domain(
                [("contract_amount", ">=", record.total_amount_untaxed)]
            )
            record.available_hr_job_ids = filtered_rules.mapped("job_ids").ids

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env["ir.actions.act_window"]._for_xml_id("base.action_attachment")
        res["domain"] = [("res_model", "=", self._name), ("res_id", "in", self.ids)]
        res["context"] = {"default_res_model": self._name, "default_res_id": self.id}
        return res

    def action_submit_approval(self):
        if self.contract_signer_id.job_id not in self.available_hr_job_ids:
            raise ValidationError(
                _(
                    "The contract signer is not allowed to sign this contract. "
                    "Please select another signer."
                )
            )

        action = super().action_submit_approval()
        if action and isinstance(action, dict) and action.get('type') == 'ir.actions.act_window':
            action["context"]["default_name"] = _(
                f"Approval {self._description} {self.name}"
            )
        return action

    def action_generate_hardcopy(self):
        pass

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_complete(self):
        self.write({"state": "done"})
