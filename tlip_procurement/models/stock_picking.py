from odoo import api, models, fields, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    contract = fields.Char('Contract')
    contract_no = fields.Char('Contract No.')
    issued_date = fields.Date('Issued Date', default=fields.Date.today)

    partner_id = fields.Many2one('res.partner', domain="[('vendor_state', '=', 'approved'), ('is_blocked', '=', False)]", tracking=True)
    vendor_legal_name = fields.Char(string="Vendor Legal Reprentative", compute="_compute_vendor", store=True)
    vendor_legal_title = fields.Char(compute="_compute_vendor", store=True)
    vendor_legal_email = fields.Char(
        compute="_compute_vendor", store=True, readonly=False
    )
    vendor_legal_fax = fields.Char(
        compute="_compute_vendor", store=True, readonly=False
    )
    vendor_legal_phone = fields.Char(
        compute="_compute_vendor", store=True, readonly=False
    )
    vendor_address_vn = fields.Char("Vendor Address (VN)", compute="_compute_vendor", store=True)
    vendor_address_en = fields.Char("Vendor Address (EN)", compute="_compute_vendor", store=True)
    vendor_legal_beneficiary = fields.Char(compute="_compute_vendor", store=True, readonly=False)
    vendor_legal_account_number = fields.Char(compute="_compute_vendor", store=True, readonly=False)
    vendor_legal_bank_id = fields.Many2one("res.bank", compute="_compute_vendor", store=True, readonly=False)
    vendor_legal_vat = fields.Char(compute="_compute_vendor", store=True)

    buyer_id = fields.Many2one('res.partner', domain="[('is_blocked', '=', False), '|', '|', ('customer_state', '=', 'approved'), ('vendor_state', '=', 'approved'), ('internal_approval_state', '=', True)]")
    buyer_legal_name = fields.Char(compute="_compute_buyer", store=True, string="'Buyer Legal Reprentative'")
    buyer_legal_title = fields.Char(compute="_compute_buyer", store=True)
    buyer_legal_email = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_fax = fields.Char(compute="_compute_buyer", store=True, readonly=False)
    buyer_legal_phone = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_vat = fields.Char(compute="_compute_buyer", store=True)
    buyer_address_vn = fields.Char("Buyer Address (VN)", compute="_compute_buyer", store=True)
    buyer_address_en = fields.Char("Buyer Address (EN)", compute="_compute_buyer", store=True)
    buyer_legal_beneficiary = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_account_number = fields.Char(
        compute="_compute_buyer", store=True, readonly=False
    )
    buyer_legal_bank_id = fields.Many2one(
        "res.bank", compute="_compute_buyer", store=True, readonly=False
    )

    for_storable_products = fields.Boolean(default=True)
    bill_id = fields.Many2one('account.move')
    user_id = fields.Many2one(copy=False)
    budget_department_responsible_job_id = fields.Many2one('hr.job', check_company=True,
                                                           compute="_compute_budget_department_responsible",
                                                           compute_sudo=True,
                                                           store=True)

    @api.depends("partner_id")
    def _compute_vendor(self):
        for record in self:
            field_mapping = {
                "vendor_legal_name": "legal_representative_name_vn",
                "vendor_legal_title": "legal_representative_title_vn",
                "vendor_legal_email": "email",
                "vendor_legal_fax": "fax",
                "vendor_legal_phone": "phone",
                "vendor_legal_vat": "vat",
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
            vendor = record.partner_id
            bank_account_info = vendor._get_default_bank_account_info() if vendor else {}
            partner_address = vendor._get_full_address_info() if vendor else {}

            for field, field_name in field_mapping.items():
                record[field] = getattr(vendor, field_name)

            for field, field_name in bank_info_mapping.items():
                record[field] = bank_account_info.get(field_name)

            for field, field_name in address_info_mapping.items():
                record[field] = partner_address.get(field_name)

    @api.depends("buyer_id")
    def _compute_buyer(self):
        for record in self:
            buyer_field_mapping = {
                "buyer_legal_name": "legal_representative_name_vn",
                "buyer_legal_title": "legal_representative_title_vn",
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

    @api.depends("purchase_id")
    def _compute_budget_department_responsible(self):
        for record in self:
            purchase_id = record.purchase_id
            requisition = purchase_id.requisition_id
            task = purchase_id.task_id

            record.budget_department_responsible_job_id = (
                requisition.budget_department_responsible_job_id or
                task.budget_department_responsible_job_id
            )

    def button_validate(self):
        for move in self.move_ids.filtered(lambda m: m.picking_type_id.code == 'incoming'):
            if move.product_uom_qty < move.quantity:
                raise UserError(_('The received quantity of product must match with the demand quantity'))

        res = super().button_validate()

        if res is True:
            for record in self.filtered(lambda r: r.purchase_id):
                purchase_order = record.purchase_id
                action = purchase_order.action_create_invoice()
                if 'invoice_ids' in action and action['invoice_ids']:
                    record.write({'bill_id': action['invoice_ids'][0]})
        return res

    def action_view_bill(self):
        self.ensure_one()
        bill_id = self.bill_id

        action = self.env['ir.actions.act_window']._for_xml_id('tlip_account.action_invoice_payment_request')
        form_res = self.env.ref('tlip_account.view_invoice_request_payment_form', False)
        action.update({
            'views': [(form_res and form_res.id or False, 'form')],
            'res_id': bill_id.id,
        })
        return action
