from markupsafe import Markup
from odoo import models, fields, Command, api, _
from odoo.exceptions import UserError, ValidationError
from ..tools.misc import format_decimal
from odoo.tools.safe_eval import safe_eval


class PurchaseContract(models.Model):
    _name = "purchase.requisition"
    _inherit = ["purchase.agreement.base", "purchase.requisition", "sign.pdf.mixin"]
    string = "Procurement Contract"

    state = fields.Selection(
        selection=[
            ("draft", "New"),
            ("review", "Reviewing"),
            ("done", "Completed"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
            ("locked", "Locked"),
        ],
        default="draft",
    )
    review_contract_state = fields.Char(
        compute="_compute_review_contract_state", store=True)
    to_review_contract = fields.Boolean(
        compute="_compute_review_contract_state", store=True)
    approval_review_ids = fields.One2many(
        'approval.review', 'requisition_id', string='Reviews')
    last_review_contract = fields.Boolean(
        compute="_compute_last_review_contract")
    final_contract = fields.Many2one('ir.attachment')
    is_final_contract_pdf = fields.Boolean(
        compute='_compute_is_final_contract_pdf', store=True)
    can_upload_final_file = fields.Boolean(compute='_compute_can_upload_final_file')
    original_contract_id = fields.Many2one(
        'purchase.requisition',
        string='Original Contract',
        copy=False,
    )
    supplement_ids = fields.One2many('purchase.supplement', 'requisition_id')
    supplement_count = fields.Integer(compute='_compute_supplment_count')
    contract_history_count = fields.Integer(compute='_compute_contract_history_count')
    task_id = fields.Many2one('procurement.task', string='Original Task')
    task_ids = fields.Many2many('procurement.task')
    currency_id = fields.Many2one('res.currency', required=True)
    total_amount_untaxed = fields.Float(
        compute='_compute_total_amount', store=True, readonly=True)
    remaining_amount = fields.Monetary(
        string='Remaining Amount', compute='_compute_remaining_amount', store=True, readonly=False)
    imported_remaing_amount = fields.Float()
    request_type = fields.Selection(related='task_id.request_type', store=True)
    payment_ids = fields.One2many(
        'account.payment', 'procurement_contract_id', string='Payments')
    checklist = fields.Html(
        name='Checklist', compute="_compute_checklist_template", store=True, readonly=False)
    remaining_amount_en_text = fields.Char(compute='_compute_format_amount')
    remaining_amount_vn_text = fields.Char(compute='_compute_format_amount')
    budget_department_responsible_job_id = fields.Many2one('hr.job', check_company=True,
                                                           compute="_compute_budget_department_responsible",
                                                           compute_sudo=True,
                                                           store=True)
    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id', readonly=True,
    )
    amount_in_currency = fields.Monetary(compute='_compute_amount_in_currency', currency_field='company_currency_id', store=True)

    @api.depends('total_amount_untaxed', 'purchase_ids.state', 'purchase_ids.amount_untaxed', 'imported_remaing_amount')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.total_amount_untaxed + record.imported_remaing_amount - sum(
                record.purchase_ids.filtered(lambda po: po.state in ('purchase', 'done')).mapped('amount_untaxed')
            )

    @api.depends('approval_request_id', 'approver_ids.status')
    def _compute_review_contract_state(self):
        for rec in self:
            review_contract_state, to_review_contract = '', False
            approval = rec.approval_request_id
            if approval:
                if any([approver.review_status == 'refused' for approver in approval.approver_ids]):
                    review_contract_state = 'Refused'
                to_review_contract = approval.to_review_contract
            rec.to_review_contract = to_review_contract
            rec.review_contract_state = review_contract_state

    @api.depends_context('uid')
    @api.depends('approver_ids.status')
    def _compute_last_review_contract(self):
        for rec in self:
            last_review_contract = False
            approval = rec.approval_request_id
            if approval.to_review_contract:
                last_2_approvers = approval.approver_ids[-2:]
                # Case last_2_approvers empty isn't exist based on constraint on approval
                previous_approved = last_2_approvers[0].status == 'approved'
                if len(last_2_approvers) < 2 or previous_approved:
                    last_approver = last_2_approvers[-1:]
                    if last_approver.status == 'pending' and self.env.user in last_approver.user_ids:
                        last_review_contract = True
            rec.last_review_contract = last_review_contract

    def _compute_supplment_count(self):
        domain = [("requisition_id.name", "in", self.mapped("name"))]
        supplement_data = self.env["purchase.supplement"]._read_group(
            domain, ["purchase_contract_name"], ["__count"]
        )
        supplement_dict = dict(supplement_data)
        for record in self:
            record.supplement_count = supplement_dict.get(record.name, 0)

    def _compute_contract_history_count(self):
        for rec in self:
            origin = rec.original_contract_id or rec
            rec.contract_history_count = self.env['purchase.requisition'].with_context(active_test=False).search_count([
                '|',
                ('id', '=', origin.id),
                ('original_contract_id', '=', origin.id),
            ])

    def action_view_contract_history(self):
        self.ensure_one()
        origin = self.original_contract_id or self
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract History'),
            'res_model': 'purchase.requisition',
            'view_mode': 'list,form',
            'domain': ['|', ('id', '=', origin.id), ('original_contract_id', '=', origin.id)],
            'context': {'active_test': False},
        }

    @api.depends("line_ids.price_total")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount_untaxed = sum(rec.line_ids.mapped("price_total"))

    def _compute_format_amount(self):
        odoo_env = self.env
        super(PurchaseContract, self)._compute_format_amount()
        for record in self:
            record.remaining_amount_vn_text = format_decimal(
                odoo_env, record.remaining_amount, lang="vi_VN")
            record.remaining_amount_en_text = format_decimal(
                odoo_env, record.remaining_amount, lang="en_US")

    @api.depends("final_contract")
    def _compute_is_final_contract_pdf(self):
        for rec in self:
            rec.is_final_contract_pdf = rec.final_contract and rec.final_contract.mimetype == 'application/pdf'

    def _compute_checklist_template(self):
        checklist_templates = self.env['checklist.template'].search([
            ('state', '=', 'confirm'),
            ('related_model_id.model', '=', self[:1]._name)
        ])
        for record in self:
            contract_checklist = False
            for checklist in checklist_templates:
                checklist_condition = safe_eval(checklist.condition)
                if record.filtered_domain(checklist_condition):
                    contract_checklist = checklist.description
                    break

            record.checklist = contract_checklist

    @api.depends('task_id', 'line_ids', 'line_ids.analytic_distribution')
    def _compute_budget_department_responsible(self):
        for record in self:
            budget_department_responsible_job = record.task_id.budget_department_responsible_job_id

            if not budget_department_responsible_job:
                budget_department_responsible_job = (
                    record.line_ids.get_department_job_on_analytic_distribution(
                        record_name=record.name,
                        company_id=record.company_id.id
                    )
                )

            record.budget_department_responsible_job_id = budget_department_responsible_job

    @api.depends('currency_id', 'company_id.currency_id', 'total_amount_untaxed', 'currency_rate')
    def _compute_amount_in_currency(self):
        for record in self:
            if record.currency_id == record.company_id.currency_id:
                record.amount_in_currency = record.total_amount_untaxed
            else:
                record.amount_in_currency = record.total_amount_untaxed * record.currency_rate

    @api.model_create_multi
    def create(self, vals_list):
        result = super(
            PurchaseContract, self
        ).create(vals_list)
        result._compute_checklist_template()
        return result

    def action_submit_approval(self):
        self.ensure_one()
        if not self.final_contract:
            raise ValidationError(_("Please upload contract hardcopy"))

        action = super().action_submit_approval()
        if action and isinstance(action, dict) and action.get('type') == 'ir.actions.act_window':
            action["context"]["default_name"] = _(
                f"Review {self._description} {self.name}")
        return action

    def _trigger_action_after_submit(self, request):
        res = super()._trigger_action_after_submit(request=request)
        self.write({"state": "review"})
        return res

    def _trigger_action_approve(self):
        approval = self.approval_request_id

        if approval and approval.to_review_contract and self.review_contract_state == 'Refused':
            self.write({"state": "draft"})
            review_list = ''
            for review in self.approval_review_ids:
                review_list += Markup('''
                                      <p>- <strong>Reason to Revise/Supplement:</strong> %s</p>
                                      <p>+ <strong>Original Clause:</strong> %s</p>
                                      <p>+ <strong>Revised Clause:</strong> %s</p>
                                      ''' % (review.reason, review.old_value, review.new_value))
            msg = _("Please review again this contract. %(review_list)s",
                    review_list=review_list
                    )
            self.message_post(body=msg)
        else:
            self.write({"state": "done"})
            for rec in self:
                task = rec.task_id
                if task.state == "contract_review":
                    task.write({"state": "approved"})

                for index, signature in rec._generate_list_approver_signatures():
                    rec.action_stamp_report(
                        signature_img=signature,
                        report_attachment=rec.final_contract,
                        direction='horizontal',
                        offset=index,
                        sig_width=25,
                        sig_height=15
                    )

    def _generate_list_approver_signatures(self):
        self.ensure_one()
        approvers = self.approval_request_id.approver_ids[:-1]
        existing_users = self.env['res.users']
        index = 0
        for approver in approvers:
            employee = approver._get_employee()
            user = employee.user_id if employee else None
            if user and user not in existing_users and employee.initial_signature_file:
                yield index, employee.initial_signature_file
                existing_users |= user
                index += 1

    def _trigger_action_cancel(self):
        if self.approval_request_id and self.approval_request_id.request_status not in ('cancel',):
            self.approval_request_id.action_cancel()
        self.write({"state": "draft"})

    def action_reject_request(self):
        self.ensure_one()
        approval = self.approval_request_id
        if approval.to_review_contract:
            approval.with_context(review_contract_refuse=True).action_approve()
        else:
            approval.action_refuse()

    def action_lock_budget(self):
        """Lock the contract and delete draft records (supplements, purchase orders)"""
        self.ensure_one()
        if self.state == 'locked':
            raise UserError(_("This contract is already locked."))

        purchases = self.purchase_ids
        if purchases.filtered(lambda p: p.state not in ('purchase', 'done', 'cancel')):
            raise UserError(_("You cannot lock contract with in-progress Purchase Order(s)"))
        purchases = purchases.filtered(lambda p: 
            bool(p.picking_ids.filtered(lambda s: s.state not in ('done', 'cancel'))) or 
            bool(p.invoice_ids.filtered(lambda inv: inv.state not in ('posted', 'cancel')))
        )
        if purchases:
            order_names = ', '.join(purchases.mapped('name'))
            raise UserError(_("This contract still has a purchase order %s that needs to be received or posted/cancelled to the vendor bills." % order_names))

        self.write({"state": "locked"})
        self.task_id.write({"is_locked": True}) # Try to lock the task as well, next time we just check task's is_locked field
        self.env['budget.reserved'].action_unreserved_amount(tasks=self.task_ids)

    def _existing_supplement(self):
        self.ensure_one()
        return self.supplement_ids.filtered(lambda r: r.state == "draft")

    def action_get_supplement_view(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "tlip_procurement.action_purchase_supplement_view"
        )
        action["domain"] = [
            ("requisition_id.name", "=", self.name),
        ]
        if self.env.context.get("show_existing_agreement"):
            action.update(
                {
                    "views": [
                        (
                            self.env.ref(
                                "tlip_procurement.purchase_supplement_view_form"
                            ).id,
                            "form",
                        )
                    ],
                    "target": "current",
                    "res_id": self._existing_supplement().id,
                }
            )
        return action

    @api.depends_context('uid')
    @api.depends('approver_ids', 'current_approver_id')
    def _compute_can_upload_final_file(self):
        for rec in self:
            current_user = self.env.user
            rec.can_upload_final_file = (
                rec.state == 'done'
                and current_user in rec.user_id
            )

    def action_open_stamp_final_contract_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Upload Final Contract'),
            'res_model': 'stamp.final.contract.wizard',
            'views': [(self.env.ref('tlip_procurement.stamp_final_contract_wizard_form_view').id, 'form')],
            'target': 'new',
            'context': {
                'default_requisition_id': self.id,
            }
        }

    def _prepare_supplement_vals(self):
        self.ensure_one()
        return {
            "requisition_id": self.id,
            "buyer_id": self.buyer_id.id,
            "buyer_street": self.buyer_street,
            "buyer_street_2": self.buyer_street_2,
            "buyer_district": self.buyer_district,
            "buyer_ward": self.buyer_ward,
            "buyer_state_id": self.buyer_state_id.id,
            "buyer_country_id": self.buyer_country_id.id,
            "vendor_id": self.vendor_id.id,
            "vendor_code": self.vendor_code,
            "vendor_street": self.vendor_street,
            "vendor_street_2": self.vendor_street_2,
            "vendor_district": self.vendor_district,
            "vendor_ward": self.vendor_ward,
            "vendor_state_id": self.vendor_state_id.id,
            "vendor_country_id": self.vendor_country_id.id,
            "vendor_vat": self.vendor_vat,
            "quotation_no": self.quotation_no,
            "quotation_date": self.quotation_date,
            "note": self.note,
            "commence_date": self.commence_date,
            "complete_date": self.complete_date,
            "estimated_month": self.estimated_month,
            "delivery_time": self.delivery_time,
            "delivery_street": self.delivery_street,
            "delivery_street_2": self.delivery_street_2,
            "delivery_district_id": self.delivery_district_id.id,
            "delivery_ward_id": self.delivery_ward_id.id,
            "delivery_state_id": self.delivery_state_id.id,
            "delivery_country_id": self.delivery_country_id.id,
            "guarantee_period": self.guarantee_period,
            "payment_frequency": self.payment_frequency,
            "payment_term_days": self.payment_term_days,
            "payment_term_description": self.payment_term_description,
            "buyer_legal_name": self.buyer_legal_name,
            "buyer_legal_title": self.buyer_legal_title,
            "buyer_legal_attoney_no": self.buyer_legal_attoney_no,
            "buyer_legal_email": self.buyer_legal_email,
            "buyer_legal_fax": self.buyer_legal_fax,
            "buyer_legal_phone": self.buyer_legal_phone,
            "buyer_legal_vat": self.buyer_legal_vat,
            "buyer_legal_beneficiary": self.buyer_legal_beneficiary,
            "buyer_legal_account_number": self.buyer_legal_account_number,
            "buyer_legal_bank_id": self.buyer_legal_bank_id.id,
            "vendor_legal_name": self.vendor_legal_name,
            "vendor_legal_title": self.vendor_legal_title,
            "vendor_legal_attoney_no": self.vendor_legal_attoney_no,
            "vendor_legal_email": self.vendor_legal_email,
            "vendor_legal_fax": self.vendor_legal_fax,
            "vendor_legal_phone": self.vendor_legal_phone,
            "vendor_legal_beneficiary": self.vendor_legal_beneficiary,
            "vendor_legal_account_number": self.vendor_legal_account_number,
            "vendor_legal_bank_id": self.vendor_legal_bank_id.id,
            "user_id": self.user_id.id,
            "contract_signer_id": self.contract_signer_id.id,
            "total_amount_untaxed": self.total_amount_untaxed,
            "currency_id": self.currency_id.id,
            "currency_rate": self.currency_rate,
            "line_ids": [
                Command.create(
                    {
                        "product_id": l.product_id.id,
                        "product_uom_id": l.product_uom_id.id,
                        "product_qty": l.product_qty,
                        "price_unit": l.price_unit,
                        "tax_rate": l.tax_rate,
                        "analytic_distribution": l.analytic_distribution,
                        "specification": l.specification,
                    }
                )
                for l in self.line_ids
            ],
        }

    def action_create_supplement(self):
        self.ensure_one()
        existing_supplement = self._existing_supplement()
        if existing_supplement:
            if existing_supplement[:1].state != "draft":
                raise UserError(
                    _("There is already an in-progress Supplement"))
            return self.with_context(
                show_existing_agreement=True
            ).action_get_supplement_view()

        supplement_vals = self._prepare_supplement_vals()
        if self.state != 'done':
            supplement_vals.update({
                'contract_appendix': True,
                'effective_date': self.complete_date
            })
        self.env["purchase.supplement"].create(supplement_vals)
        return self.with_context(
            show_existing_agreement=True
        ).action_get_supplement_view()

    def action_cancel(self):
        res = super().action_cancel()
        if self.approval_request_id:
            self.approval_request_id.action_cancel()
        return res

    def action_generate_hardcopy(self):
        self.ensure_one()
        docx_template = self.purchase_contract_type_id.document_template_id
        if not docx_template:
            return
        if not docx_template.docx_file:
            raise UserError(
                _("No DOCX file uploaded on template '%s'. Please upload a template file before generating the hard copy.")
                % docx_template.name
            )
        ctx = {
            'menu_action_id': docx_template.id,
            'active_ids': self.ids,
            'active_model': self._name,
            'skip_wizard': True,
        }
        try:
            out_data = self.env['docx.template'].with_context(
                **ctx).make_docx_pdf_report(download=False)
        except FileNotFoundError:
            raise UserError(
                _("Failed to convert the DOCX template to PDF. "
                  "Please ensure LibreOffice is installed and accessible on the server.")
            )

        if self.final_contract:
            self.final_contract.unlink()

        attachment = self.env['ir.attachment'].create({
            'name': f"{self.name}.pdf",
            'type': 'binary',
            'datas': out_data,
            'store_fname': f"{self.name}.pdf",
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        self.write({'final_contract': attachment.id})

    def action_create_purchase_order(self):
        self.ensure_one()
        # Combine tasks from task_id and task_ids
        all_tasks = self.task_id | self.task_ids

        existing_orders = self.env['purchase.order'].search([('task_id', 'in', all_tasks.ids + [False]),
                                                             ('requisition_id',
                                                              '=', self.id),
                                                             ('state', 'not in', ('cancel', 'purchase', 'done'))])

        # Create purchase orders for tasks without orders
        if not existing_orders:
            vals = []
            order_base_vals = self._prepare_purchase_order_base_vals()

            # Only allow one PO per task at the time
            tasks_without_orders = all_tasks - \
                existing_orders.mapped('task_id')
            for task in tasks_without_orders:
                vals += [{**order_base_vals,
                          "task_id": task.id,
                          "date_order": task.date_order,
                          "date_planned": task.date_planned}]

            # If no tasks without orders, use the base values from Purchase Requisition
            if not vals:
                vals = [order_base_vals]

            existing_orders = self.env['purchase.order'].create(vals)

        action = self.env['ir.actions.act_window']._for_xml_id(
            'purchase_requisition.action_purchase_requisition_to_so')
        if len(existing_orders) == 1:
            action.update({
                'res_id': existing_orders.id,
                'views': [(False, 'form')],
                "view_mode": "form",
                "view_type": "form",
                "target": "current"
            })
        else:
            action.update({
                "view_mode": "list,form",
                "domain": [("id", "in", existing_orders.ids)],
            })
        return action

    def _prepare_purchase_order_base_vals(self):
        self.ensure_one()
        return {
            "partner_id": self.vendor_id.id,
            "requisition_id": self.id,
            "company_id": self.company_id.id,
            "name": _("New"),
            "user_id": self.env.user.id,
            "currency_id": self.currency_id.id,
            "currency_rate": self.currency_rate,
            "is_order": True,
            "order_line": [
                Command.create(
                    {
                        "product_id": l.product_id.id,
                        "price_unit": l.price_unit,
                        "product_qty": l.product_qty,
                        "analytic_distribution": l.analytic_distribution,
                        "product_uom": l.product_uom_id.id,
                    }
                )
                for l in self.line_ids
            ],
        }

    def action_preview(self):
        self.ensure_one()
        wizard = self.env['pdf.review.wizard'].create({
            'pdf_document': self.final_contract.datas
        })
        return {
            'name': _('PDF Preview'),
            'view_mode': 'form',
            'res_model': 'pdf.review.wizard',
            'res_id': wizard.id,
            'views': [(self.env.ref('tlip_base.pdf_review_wizard_wizard_form_view').id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(self.env.context)
        }
