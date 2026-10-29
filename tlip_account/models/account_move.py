import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging
from itertools import groupby

from odoo import Command, _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, format_date, formatLang, float_round, get_lang
from odoo.tools.date_utils import start_of

_logger = logging.getLogger(__name__)

MAX_OVERDUE_INVOICES_COUNT = 3


def get_next_business_day(dt):
    try:
        if isinstance(dt, str):
            dt = fields.Date.from_string(dt)
        while dt.weekday() in (5, 6):
            dt += timedelta(days=1)
        return dt
    except:
        return False


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "approval.matrix.mixin", "sign.pdf.mixin"]
    _rec_names_search = ["name", "request_payment_number"]
    _description = "Journal Entry"

    partner_id = fields.Many2one(
        "res.partner",
        domain="[('is_blocked', '=', False), '|', ('parent_id', '=', False), ('is_company', '=', True), '|', '|', ('customer_state', '=', 'approved'), ('vendor_state', '=', 'approved'), ('internal_approval_state', '=', True)]",
    )
    request_payment_number = fields.Char(
        string="Resquest Payment Ref", tracking=True, copy=False
    )
    request_payment_date = fields.Date(default=fields.Date.context_today)
    is_request_payment = fields.Boolean(string="Is Request Payment", readonly=True)
    customer_contact_ids = fields.Many2many(
        "res.partner",
        relation="account_invoice_customer_contact_rel",
        column1="partner_id",
        column2="invoice_id",
        domain="[('parent_id', '=', partner_id)]",
        string="Customer Contacts",
    )

    entry_currency_rate = fields.Float(
        string="Currency Rate",
        compute="_compute_entry_currency_rate",
        inverse="_inverse_entry_currency_rate",
        store=True,
        precompute=True,
        copy=True,
        digits=(16, 2),
        help="Currency rate from company currency to document currency.",
    )
    book_exchange_rate = fields.Float(
        string="Book Exchange Rate",
        copy=False,
        digits=0,
        help="Book Exchange Rate",
    )
    deposit_payment_id = fields.Many2one(
        "account.payment",
        string="Deposit Payment",
        copy=False,
        help="Deposit Payment generated for 3 consecutive overdue payment",
    )
    is_overdue_invoice = fields.Boolean(
        string="Is Overdue Invoice",
        copy=False,
        default=False,
        store=True,
        help="Is Overdue Invoice - using for overdue report",
    )
    development_project_id = fields.Many2one(
        "development.project", string="Project", check_company=True
    )
    development_phase_id = fields.Many2one(
        "development.phase", string="Phase", check_company=True
    )
    is_monthly_evaluation = fields.Boolean(
        help="This entry will automatically reverse when opening new accounting period",
        copy=False,
    )
    invoice_type_id = fields.Many2one(
        "invoice.type", string="Request Type", tracking=True, ondelete="restrict"
    )
    invoice_type_code = fields.Selection(related="invoice_type_id.type", store=True)
    land_plot_id = fields.Many2one("stock.location")
    land_plot_name = fields.Char(
        string="Land Plot",
        compute="_compute_land_plot_name",
        store=True,
        readonly=False,
    )
    approval_readonly = fields.Boolean(compute="_compute_approval_readonly")

    contract_number = fields.Char(tracking=True)
    contract_payment_article = fields.Char()
    contract_signing_date = fields.Date(tracking=True)

    metering_point = fields.Char()
    paid_by = fields.Selection(
        selection=[("employee", "Employee"), ("company", "Company")],
        string="Paid By",
        default="company",
        tracking=True,
    )
    employee_id = fields.Many2one("res.partner", "Employee")
    oos_entry_period_id = fields.Many2one(
        "accounting.period.closing", string="OOS Entry Period", ondelete="restrict"
    )

    payment_entry_type = fields.Selection(
        [("writeoff", "Write-off"), ("currencydiff", "Currency-Diff")],
        string="Payment Entry Type",
    )

    amount_in_words_en = fields.Char(compute="_compute_amount_in_words")
    amount_in_words_vn = fields.Char(compute="_compute_amount_in_words")

    epe_non_epe = fields.Selection(related="partner_id.epe_non_epe")
    customer_code = fields.Char(related="partner_id.customer_code")
    vendor_code = fields.Char(related="partner_id.vendor_code")
    invoice_date = fields.Date(
        string="Invoice/Bill Date", index=True, copy=False, default=fields.Date.today()
    )

    partner_shipping_id = fields.Many2one(
        "res.partner",
        string="Invoicing Address",
        domain="['|', ('id', '=', partner_id), '&', ('type', '=', 'invoice'), ('parent_id', '=', partner_id)]",
    )
    available_invoice_type_ids = fields.Many2many(
        "invoice.type", compute="_compute_available_invoice_type_ids"
    )
    available_product_ids = fields.Many2many(
        "product.product", compute="_compute_available_product_ids"
    )
    minvoice_template_id = fields.Many2one(
        "minvoice.template",
        compute="_compute_minvoice_data",
        store=True,
        readonly=False,
    )
    minvoice_template_payment_method = fields.Selection(
        compute="_compute_minvoice_data", store=True, readonly=False
    )
    report_attachment_id = fields.Many2one("ir.attachment")

    parent_move_id = fields.Many2one("account.move", string="Parent Move", copy=False)
    child_move_ids = fields.One2many(
        "account.move", "parent_move_id", string="Child Moves"
    )
    child_move_count = fields.Integer(
        string="Number of Child moves", compute="_compute_child_move_count"
    )

    accounting_approval_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
        ],
        default="draft",
        tracking=True,
        copy=False,
    )
    accounting_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("wait_to_post", "Waiting to Post"),
            ("posted", "Posted"),
        ],
        compute="_compute_accounting_state",
    )
    is_accountant_user = fields.Boolean(compute="_compute_is_accountant_user")
    email_subject = fields.Char(compute="_compute_email_subject")
    email_for_payment = fields.Char()
    email_for_invoice = fields.Char()
    exclude_from_debit_credit_report = fields.Boolean(string='Exclude from Debit/Credit Report')
    tlip_entry_code = fields.Char(
        string="TLIP entry Code",
        compute="_compute_tlip_entry_code",
        store=True,
        readonly=True,
    )

    @api.depends(
        "move_type",
        "origin_payment_id",
        "origin_payment_id.payment_type",
        "journal_id",
        "journal_id.code",
        "journal_id.bank_account_id",
        "date",
        "state",
    )
    def _compute_tlip_entry_code(self):
        for move in self:
            # Skip if TLIP entry code already exists
            if move.tlip_entry_code:
                continue

            # Only posted journal entries generated from payments
            if move.state != "posted":
                continue

            if move.move_type != "entry":
                continue

            payment = move.origin_payment_id
            if not payment or payment.payment_type not in ("inbound", "outbound"):
                continue

            journal = move.journal_id
            if not journal or not journal.code:
                continue

            # Determine Bank vs Cash journal
            is_bank = bool(journal.bank_account_id)

            # Determine TLIP prefix from payment_type
            # outbound  → Vendor Payment
            # inbound   → Customer Receipt
            if payment.payment_type == "outbound":
                prefix = "PBN" if is_bank else "PCT"
            else:
                prefix = "PBC" if is_bank else "PTT"

            # Format YY/MM from accounting date
            move_date = move.date or fields.Date.context_today(self)
            yy_mm = move_date.strftime("%y/%m")

            # Monthly range
            date_from = move_date.replace(day=1)
            if move_date.month == 12:
                date_to = move_date.replace(year=move_date.year + 1, month=1, day=1)
            else:
                date_to = move_date.replace(month=move_date.month + 1, day=1)

            # Get latest TLIP code in the same month
            last_move = self.search(
                [
                    ("state", "=", "posted"),
                    ("move_type", "=", "entry"),
                    ("journal_id", "=", journal.id),
                    ("origin_payment_id", "!=", False),
                    ("date", ">=", date_from),
                    ("date", "<", date_to),
                    ("tlip_entry_code", "like", f"{prefix}-{journal.code}-{yy_mm}%"),
                ],
                order="tlip_entry_code desc",
                limit=1,
            )

            seq = "001"
            if last_move and last_move.tlip_entry_code:
                seq = str(int(last_move.tlip_entry_code[-3:]) + 1).zfill(3)

            move.tlip_entry_code = f"{prefix}-{journal.code}-{yy_mm}-{seq}"

    def _email_subject_invoice_type(self):
        return False

    def _compute_email_subject(self):
        for record in self:
            record.email_subject = record._email_subject_invoice_type()

    def _compute_child_move_count(self):
        for record in self:
            record.child_move_count = len(record.child_move_ids)

    @api.depends("invoice_type_id")
    def _compute_minvoice_data(self):
        for record in self:
            if record.invoice_type_id:
                minvoice_template_id = record.invoice_type_id.get_minvoice_template(
                    record.company_id
                ).id
            else:
                minvoice_template_id = False
            record.minvoice_template_id = minvoice_template_id
            record.minvoice_template_payment_method = (
                record.invoice_type_id.payment_method
            )

    @api.depends("invoice_type_id")
    def _compute_available_product_ids(self):
        for record in self:
            if record.invoice_type_id.product_category_ids.ids:
                domain = [
                    ("categ_id", "in", record.invoice_type_id.product_category_ids.ids),
                    ("company_id", "=", record.company_id.id),
                ]
            else:
                domain = []
            available_products = self.env["product.product"].search(domain)
            record.available_product_ids = [(6, 0, available_products.ids)]

    @api.depends_context("request_source")
    @api.depends("partner_id")
    def _compute_available_invoice_type_ids(self):
        domain = []
        if "request_source" in self.env.context:
            request_source = self.env.context["request_source"]
            if request_source == "sale":
                domain += [("type", "in", ("leasing", "service", "others"))]
            elif request_source == "utility":
                domain += [("type", "in", ("utility", "others"))]
        invoice_types = self.env["invoice.type"].search(domain)
        for record in self:
            record.available_invoice_type_ids = [(6, 0, invoice_types.ids)]

    def _compute_show_reset_to_draft_button(self):
        if self.is_tlip_accounting_accessible():
            return super()._compute_show_reset_to_draft_button()

        self.show_reset_to_draft_button = False

    @api.constrains('ref', 'state')
    def _constrains_ref_unique(self):
        for record in self:
            if not (record.ref and record.move_type in ("out_invoice", "in_invoice")):
                continue
            duplicate_ref_counts = record.search_count(
                [
                    ("ref", "=", record.ref),
                    ("company_id", "=", record.company_id.id),
                    ("state", "!=", "cancel"),
                    ("id", "!=", record.id),
                    ("move_type", "in", ("out_invoice", "in_invoice")),
                ]
            )
            if duplicate_ref_counts > 0:
                raise UserError(
                    _(
                        f"Reference '{record.ref}' already existed. Please input another one."
                    )
                )

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        def _add_readonly_condition(node):
            readonly_condition = "approval_readonly"
            if node.get("readonly"):
                node.set(
                    "readonly",
                    f"{readonly_condition} or ({node.attrib.pop('readonly')})",
                )
            else:
                node.set("readonly", readonly_condition)

        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            nodes = arch.xpath(".//field[not(ancestor::field)]")
            field_attrs = self._fields

            for node in nodes:
                if node.get("name") in ["invoice_date"]:
                    continue
                if field_attrs[node.get("name")].readonly:
                    continue
                _add_readonly_condition(node)

        return arch, view

    def _compute_amount_in_words(self):
        for record in self:
            digits = record.currency_id.decimal_places if self.currency_id else 0
            if record.currency_id:
                record.amount_in_words_en = (
                    record.currency_id.with_context(lang="en_US")
                    .amount_to_text(round(record.amount_residual, digits))
                    .capitalize()
                    .replace("dong", "Vietnamese Dong")
                )
                record.amount_in_words_vn = (
                    record.currency_id.with_context(lang="vi_VN")
                    .amount_to_text(round(record.amount_residual, digits))
                    .capitalize()
                    .replace("dong", "đồng")
                )
            else:
                record.amount_in_words_vn = False
                record.amount_in_words_en = False

    @api.depends("currency_id", "company_currency_id", "company_id", "invoice_date")
    def _compute_entry_currency_rate(self):
        for move in self:
            from_currency = move.company_currency_id
            to_currency = move.currency_id
            entry_currency_rate = 1
            if from_currency != to_currency and not move.oos_entry_period_id:
                company = move.company_id or self.env.company
                date = move.invoice_date or fields.Date.context_today(move)
                entry_currency_rate = (
                    from_currency.with_company(company)
                    .with_context(to_currency=to_currency.id, date=str(date))
                    .rate
                )
            move.entry_currency_rate = entry_currency_rate

    @api.depends("date", "auto_post", "accounting_approval_state")
    def _compute_hide_post_button(self):
        super()._compute_hide_post_button()
        for rec in self:
            rec.hide_post_button |= rec.accounting_approval_state != "approved"

    @api.depends_context("lang")
    @api.depends(
        "invoice_line_ids.currency_rate",
        "invoice_line_ids.tax_base_amount",
        "invoice_line_ids.tax_line_id",
        "invoice_line_ids.price_total",
        "invoice_line_ids.price_subtotal",
        "invoice_line_ids.price_subtotal",
        "invoice_payment_term_id",
        "partner_id",
        "currency_id",
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()

    @api.onchange("entry_currency_rate")
    def _inverse_entry_currency_rate(self):
        for record in self:
            invoice_currency_rate = 1 / record.entry_currency_rate
            record.invoice_currency_rate = invoice_currency_rate
            if record.currency_id != record.company_currency_id and not record.oos_entry_period_id:
                for line in record.line_ids:
                    if not self.env.is_protected(
                        line._fields["balance"], line
                    ) and not self.env.context.get("skip_invoice_sync"):
                        balance = line.company_id.currency_id.round(
                            line.amount_currency / invoice_currency_rate
                        )
                        line.balance = balance

    @api.depends("partner_id")
    def _compute_partner_shipping_id(self):
        non_invoice_moves = self.filtered(
            lambda move: not move.is_invoice(include_receipts=True)
        )
        super(AccountMove, non_invoice_moves)._compute_partner_shipping_id()

        for move in self - non_invoice_moves:
            # Inherit and compute partner_shipping_id with type='invoice' from partner_id
            if move.is_invoice(include_receipts=True):
                addr = move.partner_id.address_get(["invoice"])
                move.partner_shipping_id = addr and addr.get("invoice")

    @api.depends_context("uid")
    def _compute_is_accountant_user(self):
        is_accountant_user = self.env.user.has_group("account.group_account_user")
        for record in self:
            record.is_accountant_user = is_accountant_user

    def _compute_accounting_state(self):
        for record in self:
            accounting_state = "draft"
            if record.state == "posted":
                accounting_state = "posted"
            elif record.approval_state == "wait_for_approval":
                accounting_state = "wait_for_approval"
            elif record.approval_state == "approved" or not record.is_request_payment:
                accounting_state = "wait_to_post"
            record.accounting_state = accounting_state

    @api.depends("land_plot_id")
    def _compute_land_plot_name(self):
        for record in self:
            record.land_plot_name = record.land_plot_id.name

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.line_ids._conditional_add_to_compute(
            "account_id", lambda line: line.display_type == "payment_term"
        )
        for invoice in self.filtered(
            lambda move: move.move_type == "in_invoice" and move.paid_by == "employee"
        ):
            for line in invoice.line_ids:
                if line.display_type == "payment_term":
                    line.partner_id = invoice.employee_id

    def button_draft(self):
        self.action_reset_approval()
        self.action_accounting_reset_approval()
        return super().button_draft()

    def action_reset_approval(self):
        "Approval State: Rejected | Withdrawn -> Draft"
        self.write(
            {
                "approval_state": "draft",
            }
        )

    def action_accounting_reset_approval(self):
        self.write({"accounting_approval_state": "draft"})

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action["context"]["default_name"] = _(
            f"Approval Request for Request for Payment from Sales for customer {self.partner_id.name}"
        )
        return action

    @api.model
    def get_migration_moves(
        self, move_types=["in_invoice", "in_refund"], company_id=None, partner_id=None
    ):
        if company_id is None:
            company_id = self.env.company.id
        domain = [
            ("journal_id.is_migration_journal", "=", True),
            ("move_type", "in", move_types),
            ("company_id", "=", company_id),
            ("amount_residual", "!=", 0),
            ("state", "=", "posted"),
        ]
        if partner_id:
            domain.append(("partner_id", "=", partner_id))
        return self.search(domain)

    def _action_reverse(self):
        current_period = self.env[
            "accounting.period.closing"
        ]._get_current_accounting_period()
        from_date = start_of(
            current_period.accounting_period or fields.Date.today(), "month"
        )
        default_values_list = [
            {
                "date": from_date,
                "is_monthly_evaluation": move.is_monthly_evaluation,
                "book_exchange_rate": move.book_exchange_rate,
            }
            for move in self
        ]
        reverse_moves = self._reverse_moves(default_values_list)
        reverse_moves._post(soft=False)

    def _trigger_action_approve(self):
        HrEmployee = self.env["hr.employee"].browse()
        for rec in self:
            if (
                rec.is_request_payment and rec.approval_state == "approved"
            ) or not rec.is_request_payment:
                rec.write({"accounting_approval_state": "approved"})
                rec.filtered(lambda m: m.is_entry()).sudo().with_context(
                    force_post=True
                ).action_post()

            if rec.is_request_payment and rec.approval_state != "approved":
                rec.write({"approval_state": "approved"})
                if rec.invoice_type_id and rec.invoice_type_id.request_sequence_id:
                    rec._generate_pdf_report()
                    final_approver = rec.approver_ids[-1] if rec.approver_ids else rec.approver_ids
                    employee = final_approver._get_employee() if final_approver else HrEmployee
                    if not employee and not self.env.context.get("manual_bypass_approve", False):
                        raise UserError(
                            _("No employee found for the current user in the specified job position %s. "
                            "Please assign an employee to the user.") % final_approver.user_id.name
                        )

                    rec.action_stamp_report(signature_img=employee.e_signature_file)

    def _trigger_action_refuse(self):
        for rec in self:
            if rec.is_request_payment and rec.approval_state != "approved":
                rec.write({"approval_state": "rejected"})
            if (
                rec.is_request_payment and rec.approval_state == "approved"
            ) or not rec.is_request_payment:
                rec.write({"accounting_approval_state": "rejected"})

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        for rec in self:
            if rec.is_request_payment and rec.approval_state != "approved":
                rec.write({"approval_state": "wait_for_approval"})
            else:
                rec.write({"accounting_approval_state": "wait_for_approval"})
        return result

    def _trigger_action_withdraw(self, reason: str):
        for rec in self:
            if (
                rec.is_request_payment
                and rec.approval_state != "approved"
                and rec.accounting_approval_state == "draft"
            ):
                rec.write({"approval_state": "withdrawn"})
            else:
                rec.write({"accounting_approval_state": "withdrawn"})
        super()._trigger_action_withdraw(reason)

    def _validate_submit_approval(self):
        soft = True
        validation_msgs = self._prepare_validation_msgs_approval(soft=soft)
        if validation_msgs:
            hyphenated_symbol = "- " if len(validation_msgs) > 1 else ""
            msg = "\n\n".join([hyphenated_symbol + line for line in validation_msgs])
            raise UserError(msg)

    def _prepare_validation_msgs_approval(self, soft=True):
        validation_msgs = list()
        for invoice in self.filtered(lambda move: move.is_invoice(include_receipts=True)):
            if (
                invoice.quick_edit_mode
                and invoice.quick_edit_total_amount
                and invoice.currency_id.compare_amounts(
                    invoice.quick_edit_total_amount, invoice.amount_total
                )
                != 0
            ):
                validation_msgs.append(_(
                    "The current total is %(current_total)s but the expected total is %(expected_total)s. In order to post the invoice/bill, "
                    "you can adjust its lines or the expected Total (tax inc.).",
                    current_total=formatLang(
                        self.env, invoice.amount_total, currency_obj=invoice.currency_id),
                    expected_total=formatLang(
                        self.env, invoice.quick_edit_total_amount, currency_obj=invoice.currency_id),
                ))
            if invoice.partner_bank_id and not invoice.partner_bank_id.active:
                validation_msgs.append(_(
                    "The recipient bank account linked to this invoice is archived.\n"
                    "So you cannot confirm the invoice."
                ))
            if float_compare(invoice.amount_total, 0.0, precision_rounding=invoice.currency_id.rounding) < 0:
                validation_msgs.append(_(
                    "You cannot validate an invoice with a negative total amount. "
                    "You should create a credit note instead. "
                    "Use the action menu to transform it into a credit note or refund."
                ))

            if not invoice.partner_id:
                if invoice.is_sale_document():
                    validation_msgs.append(
                        _("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif invoice.is_purchase_document():
                    validation_msgs.append(
                        _("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            if not invoice.invoice_date:
                if invoice.is_sale_document(include_receipts=True):
                    invoice.invoice_date = fields.Date.context_today(self)
                elif invoice.is_purchase_document(include_receipts=True):
                    validation_msgs.append(
                        _("The Bill/Refund date is required to validate this document."))

        self.line_ids.with_context(
            validate_analytic=True
        )._validate_analytic_distribution()
        for move in self:
            if move.state in ['posted', 'cancel']:
                validation_msgs.append(
                    _('The entry %(name)s (id %(id)s) must be in draft.', name=move.name, id=move.id))
            if not move.line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')):
                validation_msgs.append(
                    _('You need to add a line before submitting.'))
            if not soft and move.auto_post != 'no' and move.date > fields.Date.context_today(self):
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                validation_msgs.append(
                    _("This move is configured to be auto-posted on %(date)s", date=date_msg))
            if not move.journal_id.active:
                validation_msgs.append(_(
                    "You cannot submit an entry in an archived journal (%(journal)s)",
                    journal=move.journal_id.display_name,
                ))
            if move.display_inactive_currency_warning:
                validation_msgs.append(_(
                    "You cannot validate a document with an inactive currency: %s",
                    move.currency_id.name
                ))

            if move.line_ids.account_id.filtered(lambda account: account.deprecated) and not self._context.get('skip_account_deprecation_check'):
                validation_msgs.append(
                    _("A line of this move is using a deprecated account, you cannot post it."))

            if move.move_type in ['in_invoice', 'in_refund']:
                if not all(move.invoice_line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')).mapped("analytic_distribution")):
                    validation_msgs.append(_("All lines must have a Budget Code before submitting for approval."))

            # Validate remaining budget for vendor bills and journal entries
            # if move.move_type in ["in_invoice", "in_refund", "entry"]:
            #     budget_validation_errors = move._validate_remaining_budget()
            #     validation_msgs.extend(budget_validation_errors)

            # If the field autocheck_on_post is set, we want the checked field on the move to be checked
            move.checked = move.journal_id.autocheck_on_post

        return validation_msgs

    def _validate_remaining_budget(self):
        """
        Validate that each budget code (analytic account) has sufficient remaining budget.
        Returns a set of error messages if any budget is insufficient.
        """
        self.ensure_one()
        validation_errors = []

        # Get lines with analytic distribution (debit lines for vendor bills, or lines with positive amounts for JE)
        lines_to_check = self.line_ids.filtered(
            lambda l: (
                l.analytic_distribution
                and l.display_type not in ("line_section", "line_note")
            )
        )
        budget_amounts = self._calculate_budget_amounts_from_lines(lines_to_check)
        if not budget_amounts:
            return validation_errors

        validation_errors = self._validate_remaining_budget_on_budget_account(
            budget_amounts
        )

        return validation_errors

    def _calculate_budget_amounts_from_lines(self, lines):
        self.ensure_one()
        if not lines:
            return {}

        # Aggregate amounts by analytic account
        budget_amounts = {}
        for line in lines:
            if not line.analytic_distribution:
                continue

            # For vendor bills, we check debit amounts (expenses)
            # For journal entries, we check debit amounts
            line_amount = abs(line.balance) if line.debit > 0 else 0

            if line_amount == 0:
                continue

            for account_id_str, percentage in line.analytic_distribution.items():
                account_id = int(account_id_str)
                amount = line_amount * (percentage / 100)
                budget_amounts[account_id] = budget_amounts.get(account_id, 0) + amount

        return budget_amounts

    def _validate_remaining_budget_on_budget_account(self, budget_amounts):
        validation_errors = []

        # Check remaining budget for each account
        analytic_accounts = self.env["account.analytic.account"].browse(
            list(budget_amounts.keys())
        )

        for account in analytic_accounts:
            required_amount = budget_amounts.get(account.id, 0)
            remained_amount = account.remained_amount
            reserved_amount = self._to_validate_with_reserved_amount(account)
            remained_amount += reserved_amount

            if float_compare(required_amount, remained_amount, precision_rounding=self.currency_id.rounding) > 0:
                validation_errors.append(
                    _("Insufficient budget for '%(account)s': Required %(required)s but only %(remained)s remaining.",
                      account=account.display_name,
                      required=formatLang(self.env, required_amount, currency_obj=self.currency_id),
                      remained=formatLang(self.env, remained_amount, currency_obj=self.currency_id))
                )

        return validation_errors

    def _to_validate_with_reserved_amount(self, account):
        self.ensure_one()
        return 0

    def action_create_request_payment_report(self):
        self.ensure_one()
        self._generate_pdf_report()

    def _compute_approval_readonly(self):
        for rec in self:
            # Accountant is allowed to edit when approval_state is processing and accounting_approval_state is draft
            rec.approval_readonly = (
                rec.state != "draft"
                or rec.accounting_approval_state != "draft"
                or (rec.approval_state != "draft" and not rec.is_accountant_user)
            )

    def _post(self, soft=True):
        # To bypass period closing for customer import data
        trusted = self.env.su or self.env.user.has_group(
            'tlip_access_rights.group_tlip_chief_account') or self.env.user.has_group(
            'account.group_account_manager')
        if not (trusted and self.env.context.get('bypass_period_closing')):
            current_period = self.env['accounting.period.closing']._get_current_accounting_period(
            )
            for invoice in self.filtered(lambda move: not move.asset_id):
                current_period.validate_accounting_date(invoice.date)

        trusted = self.env.su or self.env.user.has_group(
            'tlip_access_rights.group_tlip_chief_account') or self.env.user.has_group(
            'account.group_account_manager')
        if not self.env.user.has_groups(
            "account.group_account_user"
        ) and not (trusted and self.env.context.get("force_post")):
            raise ValidationError(_("You do not have permission to post journal entry"))

        self = self.with_context(skip_change_partner=True)
        return super(AccountMove, self)._post(soft=soft)

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        if (
            self.env.context.get("skip_change_partner")
            and partner_ids
            and self.partner_id.id in partner_ids
        ):
            partner_ids.remove(self.partner_id.id)

        return super().message_subscribe(
            partner_ids=partner_ids, subtype_ids=subtype_ids
        )

    def _generate_report_payment_request(self):
        self.ensure_one()
        self = self.with_context(active_test=False)
        partner_address = (
            self.partner_id._get_full_address_info() if self.partner_id else {}
        )

        request_payment_number = self.request_payment_number
        if not request_payment_number:
            request_sequence = self.invoice_type_id.request_sequence_ids.filtered(
                lambda r: r.company_id == self.company_id
            )[:1]

            if request_sequence:
                request_payment_number = request_sequence._next()
                self.write({"request_payment_number": request_payment_number})

        digits = self.currency_id.decimal_places if self.currency_id else 0
        vals = {
            "request_payment_number": request_payment_number or "",
            "partner_name_vn": self.partner_id.name,
            "partner_name_en": self.partner_id.name_en,
            "partner_address_vn": partner_address.get("partner_address_vn", ""),
            "partner_address_en": partner_address.get("partner_address_en", ""),
            "partner_code": self.partner_id.customer_code
            if self.is_invoice(True)
            else self.partner_id.vendor_code,
            "vat": self.partner_id.vat,
            "business_type": "EPE"
            if self.partner_id.epe_non_epe == "epe"
            else "Non-EPE",
            "contract_payment_article": self.contract_payment_article,
            "contract_number": self.contract_number,
            "contract_signing_date": format_date(self.env, self.contract_signing_date),
            "amount_in_words_en": self.amount_in_words_en,
            "amount_in_words_vn": self.amount_in_words_vn,
            "invoice_lines": self._generate_report_payment_request_line(),
            "tax_rate": formatLang(
                self.env, self.line_ids.tax_ids[:1].amount, digits=0
            ),
            "amount_untaxed": formatLang(
                self.env, float_round(self.amount_untaxed, digits), digits=digits
            ),
            "amount_tax": formatLang(
                self.env, float_round(self.amount_tax, digits), digits=digits
            ),
            "amount_total": formatLang(
                self.env, float_round(self.amount_total, digits), digits=digits
            ),
            "paid_amount": formatLang(
                self.env,
                float_round(self.amount_total - self.amount_residual, digits),
                digits=digits,
            ),
            "amount_residual": formatLang(
                self.env, float_round(self.amount_residual, digits), digits=digits
            ),
            "due_date": format_date(self.env, self.invoice_date_due),
            "company_bank_accounts": self.company_id.with_context(
                active_test=True
            )._get_bank_account_info(),
            'date': format_date(self.env, self.invoice_date),
            "currency": self.currency_id.name,
            "metering_point": self.metering_point,
        }
        return vals

    def _generate_report_payment_request_line(self):
        vals = []
        for index, line in enumerate(
            self.with_context(active_test=False).invoice_line_ids, start=1
        ):
            data = line._generate_report_payment_request()
            data["index"] = index
            vals += [data]
        return vals

    @api.model
    def _run_oos_sync(self, company, month, year, oos_entry_period=None):
        oos_entry_period = (
            oos_entry_period
            or self.env["accounting.period.closing"]._get_current_accounting_period()
        )
        journal = company.hrms_journal_id
        oss_mappings = (
            self.env["oos.mapping"].sudo().search([("company_id", "=", company.id)])
        )
        item_codes = set(oss_mappings.mapped("item_code"))
        codes = [f"'{code}'" for code in item_codes]
        credential_data = company._get_credential_data("hrms")
        database = credential_data.get("database")
        sql_query = f"""
            SELECT [HachToanID]
                ,[Thang]
                ,[Nam]
                ,[MaKhoanMuc]
                ,[MaKhoanMucKeToan]
                ,[TenKhoanMuc]
                ,[NhomNhanVien]
                ,[MaChiTieu]
                ,[TenChiTieuCanLay]
                ,[VND]
                ,[USD]
                ,[DoiTuong]
                ,[Status]
                ,[TyGia]
            FROM [{database}].[dbo].[NS_TL_HachToan]
            WHERE Thang = '{f"{int(month):02d}"}' AND Nam = '{year}'
            AND CongTyID = '{company.hrms_company_id}';
        """
        datas, msg = company._execute_mssql_query(credential_data, sql_query)
        if msg != "Success":
            raise ValidationError(msg)
        journal_entries = {}
        invoice_date = (date(int(year), int(month), 1) + relativedelta(months=1)) - relativedelta(days=1)

        for data in datas:
            MaChiTieu = data.get("MaChiTieu")
            DoiTuong = data.get("DoiTuong")
            MaKhoanMuc = data.get("MaKhoanMuc", False)
            MaKhoanMucKeToan = data.get("MaKhoanMucKeToan", False)
            data["USD"] = float(data["USD"])
            data["VND"] = float(data["VND"])
            data["TyGia"] = float(data["TyGia"])

            # 4.2. Cập nhật bút toán sync OOS USD VND
            # if float_compare(data['USD'], 0, 2) != 0 and float_compare(data['VND'], 0, 2) == 0:
            #     data['VND'] = data['USD'] * data['TyGia']

            currency = "VND"
            if float_compare(data["USD"], 0, 2) != 0:
                currency = "USD"

            currency_id = (
                self.env.ref("base.USD").id
                if currency == "USD"
                else company.currency_id.id
            )
            journal_entry_key = f"{DoiTuong}-{currency}"
            journal_entry = journal_entries.get(
                journal_entry_key,
                {
                    "company_id": company.id,
                    "journal_id": journal.id,
                    "entry_currency_rate": data["TyGia"] if currency == "USD" else 1,
                    "ref": f"Salary Slip of {DoiTuong} for {'%02d' % month}/{year}",
                    "currency_id": currency_id,
                    "oos_entry_period_id": oos_entry_period.id,
                    "line_ids": [],
                    "date": invoice_date,
                },
            )

            domain = [("item_code", "=", MaChiTieu)]
            if MaKhoanMuc or MaKhoanMucKeToan:
                domain += [("budget_code_id.code", "in", list(filter(bool, [MaKhoanMuc, MaKhoanMucKeToan])))]
            oos_mapping = oss_mappings.filtered_domain(domain)
            if not oos_mapping or (MaChiTieu == "TLLT" and not MaKhoanMuc and not MaKhoanMucKeToan):
                continue

            journal_items = journal_entry["line_ids"]
            journal_items += self._generate_entry_lines(oos_mapping, data, currency_id)
            journal_entry["line_ids"] = journal_items
            journal_entries[journal_entry_key] = journal_entry

        self.env["account.move"].sudo().with_context(
            # reduce other sync side effects
            skip_invoice_sync=True,
        ).create(list(journal_entries.values()))

    @api.model
    def _synchronize_hrms_data(self, date=fields.Datetime.now()):
        month = date.month
        year = date.year
        companies = (
            self.env["res.company"].sudo().search([("hrms_server", "!=", False)])
        )
        for company in companies:
            self._run_oos_sync(company, month, year)
        return True

    @api.model
    def _generate_entry_lines(self, oos_mapping, data, currency_id):
        analytic_distribution = None
        if oos_mapping.budget_account_id:
            analytic_distribution = {oos_mapping.budget_account_id.id: 100}

        usd = data.get("USD", 0.0)
        vnd = data.get("VND", 0.0)

        has_usd = float_compare(usd, 0.0, precision_digits=2) != 0
        has_vnd = float_compare(vnd, 0.0, precision_digits=2) != 0
        currency_rate = data.get("TyGia", 1.0)
        company_currency = self.env.company.currency_id.id

        base_vals = {
            "name": oos_mapping.description,
            "analytic_distribution": analytic_distribution,
        }

        debit_vals = base_vals.copy()
        credit_vals = base_vals.copy()

        credit_vals.update(
            {
                "debit": 0.0,
                "credit": vnd,
                "account_id": oos_mapping.credit_account_id.id,
                "partner_id": oos_mapping.partner_credit_id.id
                or oos_mapping.partner_debit_id.id,
            }
        )
        debit_vals.update(
            {
                "debit": vnd,
                "credit": 0.0,
                "account_id": oos_mapping.debit_account_id.id,
                "partner_id": oos_mapping.partner_debit_id.id
                or oos_mapping.partner_credit_id.id,
                "oos_mapping_id": oos_mapping.id,
            }
        )

        if has_usd:
            credit_vals.update(
                {
                    "currency_id": currency_id,
                    "amount_currency": -usd,
                    "credit": usd * currency_rate if not has_vnd else vnd,
                }
            )
            debit_vals.update(
                {
                    "currency_id": currency_id,
                    "amount_currency": usd,
                    "debit": usd * currency_rate if not has_vnd else vnd,
                }
            )

        return [
            Command.create(debit_vals),
            Command.create(credit_vals),
        ]

    def action_confirm_expense(self):
        self.ensure_one()
        expense_move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "company_id": self.company_id.id,
                "currency_id": self.currency_id.id,
                "line_ids": [
                    Command.create(
                        {
                            "name": line.name,
                            "partner_id": line.partner_id.id,
                            "amount_currency": line.amount_currency,
                            "currency_id": line.currency_id.id,
                            "account_id": line.account_id.id,
                        }
                    )
                    for line in self.line_ids
                ],
                "parent_move_id": self.id,
            }
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_journal_line"
        )
        action.update(
            {
                "view_type": "form",
                "res_id": expense_move.id,
                "view_mode": "form",
                "views": [(False, "form")],
            }
        )
        return action

    @api.model
    def _check_overdue_invoices(self):
        """
        Check overdue invoices and create deposit invoices for partners with 3 or more overdue invoices
        of the same invoice type.
        """
        overdue_invoices = self.search(
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("invoice_date_due", "<", fields.Date.today()),
                ("deposit_payment_id", "=", False),
            ]
        )
        overdue_invoices.is_overdue_invoice = True
        partner_invoices = []
        overdue_invoices_sorted = sorted(
            overdue_invoices, key=lambda inv: (inv.partner_id, inv.invoice_type_id)
        )
        for (partner, invoice_type), invoices in groupby(
            overdue_invoices_sorted,
            key=lambda inv: (inv.partner_id, inv.invoice_type_id),
        ):
            invoices = self.env["account.move"].concat(*invoices)
            if len(invoices) < MAX_OVERDUE_INVOICES_COUNT:
                continue

            consecutive_invoice_groups = invoices._find_consecutive_unpaid_invoices()
            _logger.info(
                f"Processing overdue invoices for partner {partner.name} with {len(invoices)} invoices of type {invoice_type.name_en} with consecutive groups {consecutive_invoice_groups}"
            )
            for invoice_group in consecutive_invoice_groups:
                partner_invoices.append((partner, invoice_type, invoice_group))

        if partner_invoices:
            self._create_deposit_payments(partner_invoices)

    def _find_consecutive_unpaid_invoices(self):
        """
        Find groups of 3 consecutive unpaid invoices (where residual_amount > 0).

        Returns:
            List of lists, where each inner list contains 3 consecutive unpaid invoice IDs
        """
        # Get list of unpaid invoice IDs
        sorted_invoices = self.sorted(key=lambda inv: inv.invoice_date_due)

        # Map invoice IDs to their residual amounts
        invoice_residual = {
            invoice.id: invoice.amount_residual for invoice in sorted_invoices
        }

        results = []
        consecutive = []
        for invoice_id, residual_amount in invoice_residual.items():
            if residual_amount > 0:
                consecutive.append(invoice_id)
            else:
                consecutive = []

            if len(consecutive) == MAX_OVERDUE_INVOICES_COUNT:
                results.append(consecutive)
                consecutive = []
        return results

    def _create_deposit_payments(self, partner_invoices: list[tuple]):
        deposit_percent_amount = self.env.company.deposit_percent_amount
        if not deposit_percent_amount:
            _logger.warning(
                "Deposit percent amount is not set. Skipping deposit payment creation."
            )
            return

        payment_vals_list = []
        for partner, invoice_type, invoices in partner_invoices:
            invoices = self.env["account.move"].browse(invoices)
            amount = (
                sum(invoices.mapped("amount_residual")) * deposit_percent_amount / 100
            )
            payment_vals = {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": partner.id,
                "amount": amount,
                "due_date": fields.Date.today(),
                # 'journal_id': self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
                # 'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                "invoice_ids": [(6, 0, invoices.ids)],
                "overdue_move_ids": [(6, 0, invoices.ids)],
            }
            payment_vals_list.append(payment_vals)
            _logger.info(
                f"Creating deposit payment for partner {partner.name} with overdue invoices {invoices.mapped('name')} of type {invoice_type.name_en}"
            )
        self.env["account.payment"].create(payment_vals_list)

    def _generate_pdf_report(self):
        attachments = self.env["ir.attachment"]
        for record in self.filtered(
            lambda r: (
                r.is_request_payment and r.invoice_type_id.report_payment_request_id
            )
        ):
            if record.invoice_type_id.report_payment_request_id.model != "account.move":
                if self.env.context.get("skip_report_generation_check", True):
                    continue

                raise UserError(
                    _(
                        f"The report invoice request from invoice type {record.invoice_type_id.display_name} must be 'account.move'. Please contact your administrator."
                    )
                )

            report = record.invoice_type_id.report_payment_request_id
            pdf = self.env["ir.actions.report"]._render_qweb_pdf(report, record.id)
            filename = f"{record.request_payment_number}" + ".pdf"
            report_attachment_id = attachments.create(
                {
                    "name": filename,
                    "type": "binary",
                    "datas": base64.b64encode(pdf[0]),
                    "store_fname": filename,
                    "res_model": self._name,
                    "res_id": record.id,
                    "mimetype": "application/pdf",
                }
            )
            attachments |= report_attachment_id

            if record.report_attachment_id:
                record.report_attachment_id.unlink()

            record.write({"report_attachment_id": report_attachment_id.id})

        return attachments

    def action_view_child_moves(self):
        if self.move_type == "out_invoice":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_out_invoice_type"
            )
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_journal_line"
            )
        action["domain"] = [("id", "in", self.child_move_ids.ids)]
        return action

    def action_open_mail_composer(self):
        self.ensure_one()
        template = self._find_mail_template()

        # Use only the generated report attachment instead of all attachments
        attachment_ids = []
        if self.report_attachment_id:
            attachment_ids = [self.report_attachment_id.id]

        composer_vals = {
            'default_model': 'account.move',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'email_notification_allow_footer': True,
            'default_template_id': template.id,
            'default_attachment_ids': [(6, 0, attachment_ids)],
            'force_email': True,
            'default_mail_server_id': self.company_id.invoice_mail_server_id.id
        }

        return {
            "name": "Send Email",
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": composer_vals,
        }

    @api.model
    def _find_mail_template(self):
        return self.invoice_type_id.default_email_template_id or self.env.ref(
            "account.email_template_edi_invoice", raise_if_not_found=False
        )

    def _get_email_to(self):
        self.ensure_one()
        if self.email_for_payment or self.email_for_invoice:
            return self.email_for_payment or self.email_for_invoice
        contacts = self.customer_contact_ids or self.partner_shipping_id
        emails = list(filter(bool, contacts.mapped('email')))
        email_to = ','.join(emails)
        return email_to

    def action_multi_send(self):
        template = self._find_mail_template()
        default_email_address = self.env['ir.mail_server']._get_default_from_address(
        )
        for record in self:
            template.with_user(SUPERUSER_ID).with_delay().send_mail(record.id, force_send=False, email_values={
                'email_to': record._get_email_to(),
                'email_from': default_email_address,
                'attachment_ids': record.report_attachment_id.ids
            })

    @api.model
    def publish_minvoices(self, invoices, action="save"):
        for invoice in invoices:
            if not invoice.minvoice_template_id:
                invoice.message_post(
                    body=_(
                        "No M-Invoice template configured for this invoice. Please update the invoice to add a template."
                    )
                )
                continue
            minvoice_action_wizard = self.env["minvoice.action.wizard"].create(
                {
                    "move_id": invoice.id,
                    "minvoice_issued_date": datetime.now().replace(microsecond=0),
                    "minvoice_template_id": invoice.minvoice_template_id.id,
                    "minvoice_template_code": invoice.minvoice_template_code,
                    "minvoice_template_payment_method": invoice.minvoice_template_payment_method,
                    "minvoice_action": action,
                }
            )
            try:
                minvoice_action_wizard.button_do_action_minvoice()
            except Exception as e:
                invoice.message_post(body=_("Failed to publish M-Invoice: %s" % str(e)))
                _logger.exception(
                    "Failed to publish M-Invoice for invoice %s: %s", invoice.id, str(e)
                )
        return True

    @api.model
    def is_tlip_accounting_accessible(self):
        accounting_access_groups = self.env.ref('accountant.menu_accounting').groups_id
        return bool(accounting_access_groups & self.env.user.groups_id)

    def _prepare_minvoice_wizard_vals(self):
        vals = super()._prepare_minvoice_wizard_vals()
        if self.invoice_type_id:
            template = self.invoice_type_id.get_minvoice_template(self.company_id)
            if template:
                vals.update(
                    self._get_minvoice_template_vals(
                        template_id=template, default_text="default_"
                    )
                )
        return vals

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        base_line = super()._prepare_product_base_line_for_taxes_computation(
            product_line
        )

        if product_line.tax_excluded:
            base_line["tax_excluded"] = product_line.tax_excluded

        if self.invoice_type_id.type == "leasing":
            price_unit = product_line.leasing_price_unit
            if (
                product_line.product_uom_id.leasing_type
                and "m2" in product_line.product_uom_id.leasing_type
            ):
                price_unit = product_line.leasing_price_unit * product_line.area

            # To solve the rounding issue, subtotal = leasing_price_unit * quantity * area
            # But leasing_price_unit=0.25, quantity=4, area=110.5, and we compute_price_unit individually will give subtotal=110.48 instead of 110.5
            new_base_line = self._prepare_product_base_line_for_leasing_price(
                product_line, price_unit
            )
            base_line["price_unit"] = new_base_line["price_unit"]

        return base_line

    def _prepare_product_base_line_for_leasing_price(self, product_line, price_unit):
        self.ensure_one()
        is_invoice = self.is_invoice(include_receipts=True)
        sign = self.direction_sign if is_invoice else 1
        if is_invoice:
            rate = self.invoice_currency_rate
        else:
            rate = (
                (abs(product_line.amount_currency) / abs(product_line.balance))
                if product_line.balance
                else 0.0
            )

        return self.env["account.tax"]._prepare_base_line_for_taxes_computation(
            product_line,
            price_unit=price_unit,
            quantity=product_line.quantity if is_invoice else 1.0,
            discount=product_line.discount if is_invoice else 0.0,
            rate=rate,
            sign=sign,
            special_mode=False if is_invoice else "total_excluded",
        )

    @api.model
    def create(self, vals):
        if vals.get("invoice_date_due"):
            is_utility = (
                vals.get("invoice_type_id")
                and self.env["invoice.type"].browse(vals["invoice_type_id"]).type
                == "utility"
            )
            if not is_utility:
                vals["invoice_date_due"] = get_next_business_day(
                    vals["invoice_date_due"]
                )
        record = super().create(vals)
        if (
            record.invoice_type_id
            and record.is_request_payment
            and not record.request_payment_number
        ):
            request_sequence = record.invoice_type_id.request_sequence_ids.filtered(
                lambda r: r.company_id == record.company_id
            )[:1]

            if request_sequence:
                request_payment_number = request_sequence._next()
                record.write({"request_payment_number": request_payment_number})
        if record.invoice_type_id and not record.minvoice_template_id:
            record._compute_minvoice_data()

        return record

    def write(self, vals):
        res = super().write(vals)
        if 'invoice_date_due' in vals and vals['invoice_date_due']:
            if not any(r.invoice_type_id.type != 'utility' for r in self):
                vals['invoice_date_due'] = get_next_business_day(vals['invoice_date_due'])
        if vals.get('invoice_type_id') and self.request_payment_number:
            # For quick workaround
            raise UserError(_("You cannot change the invoice type of a record since it already has a request payment number."))

        return res

    def job_recompute_invoice_type_taxes(self):
        for move in self:
            prev_state = move.state
            prev_accounting_approval_state = move.accounting_approval_state
            if prev_state in ("posted", "cancel"):
                move.button_draft()

            if move.invoice_type_id.tax_calculation_rounding_method != "round_globally":
                continue

            line_taxes = {
                line.id: line.tax_ids.ids
                for line in move.invoice_line_ids
                if line.tax_ids
            }
            if not line_taxes:
                continue

            move.write(
                {
                    "invoice_line_ids": [
                        Command.update(lid, {"tax_ids": [Command.clear()]})
                        for lid in line_taxes
                    ]
                }
            )
            move.write(
                {
                    "invoice_line_ids": [
                        Command.update(lid, {"tax_ids": [Command.set(tids)]})
                        for lid, tids in line_taxes.items()
                    ]
                }
            )

            move.action_post()

    @api.model
    def _cron_update_tlip_entry_code(self):
        moves = self.search(
            [
                ("state", "=", "posted"),
                ("move_type", "=", "entry"),
                ("origin_payment_id", "!=", False),
                # ("tlip_entry_code", "=", False),
            ]
        )

        for move in moves.sorted(key=lambda m: (m.date, m.id)):
            move._compute_tlip_entry_code()

    def job_cancel_move(self):
        for move in self:
            if move.state != "posted":
                continue
            move.line_ids.remove_move_reconcile()
            move_no_check = move.with_context(check_move_validity=False)
            move_no_check.button_draft()
            move_no_check.button_cancel()
