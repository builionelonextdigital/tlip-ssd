import base64
from datetime import date

from odoo import api, fields, models, _, Command
from odoo.tools import float_is_zero, format_date, formatLang
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from .account_move import get_next_business_day
from odoo.osv import expression


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["account.payment", "approval.matrix.mixin", "analytic.mixin", "sign.pdf.mixin"]
    _rec_names_search = ["name", "request_payment_number"]
    _description = "Payments"

    is_request_payment = fields.Boolean(string="Is Request Payment", readonly=True)
    is_advance_payment = fields.Boolean(string="Is Advance Payment", readonly=True)
    request_payment_number = fields.Char(tracking=True, copy=False)
    invoice_type_id = fields.Many2one(
        'invoice.type', string="Request Type", tracking=True, ondelete='restrict')
    available_reconcile_item_ids = fields.Many2many(
        "account.move.line",
        compute_sudo=True,
        compute="_compute_available_reconcile_item_ids",
    )
    auto_reconcile_item_ids = fields.Many2many(
        "account.move.line",
        relation="payment_auto_reconcile_item_rel",
        column1="payment_id",
        column2="reconcile_item_id",
        copy=False,
        string="Reconcile"
    )
    foreign_currency_id = fields.Many2one('res.currency')
    entry_amount_currency = fields.Monetary(
        string='Amount in Currency',
        currency_field="foreign_currency_id",
        copy=False)
    entry_currency_rate = fields.Float(
        string='Currency Rate',
        copy=False,
        compute='_compute_entry_amount_currency',
        digits=0,
        store=True,
        readonly=False,
        help="Currency rate from company currency to document currency.",
    )
    approval_readonly = fields.Boolean(compute="_compute_approval_readonly")
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        compute='_compute_destination_account_id',
        domain="[('account_type', 'in', ('asset_receivable', 'asset_non_current', 'liability_payable', 'liability_current'))]",
        check_company=True)
    move_ids = fields.One2many(
        'account.move', 'origin_payment_id', string='Journal Entries')
    overdue_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='deposit_payment_id',
        string='Overdue Invoices',
        domain=[('state', '=', 'posted'), ('move_type', '=', 'out_invoice')],
    )
    development_project_id = fields.Many2one(
        'development.project', string='Project', check_company=True)
    development_phase_id = fields.Many2one(
        'development.phase', string='Phase', check_company=True)

    contract_number = fields.Char(tracking=True)
    contract_payment_article = fields.Char()
    contract_signing_date = fields.Date(tracking=True)
    due_date = fields.Date(string='Due Date')
    confirmed_due_date = fields.Date(string='Confirmed Due Date')
    epe_non_epe = fields.Selection(related='partner_id.epe_non_epe')
    customer_code = fields.Char(related='partner_id.customer_code')
    vendor_code = fields.Char(related='partner_id.vendor_code')

    tax_account_id = fields.Many2one('account.account', string='Tax Account')
    amount_in_words_en = fields.Char(compute='_compute_amount_in_words')
    amount_in_words_vn = fields.Char(compute='_compute_amount_in_words')

    journal_entry_currency_id = fields.Many2one(
        'res.currency', string='Journal Currency', compute='_compute_journal_entry_currency_id')
    # == Payment difference fields == #
    show_diff_in_currency = fields.Boolean(
        compute='_compute_show_diff_in_currency')
    diff_in_currency = fields.Monetary(
        compute='_compute_diff_in_currency', store=True)
    writeoff_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Difference Account",
        copy=False,
        domain="[('deprecated', '=', False)]",
        check_company=True,
    )

    writeoff_label = fields.Char(
        string='Journal Item Label', default='Write-Off')
    diff_in_currency_handling = fields.Selection(string="Payment Difference Handling",
                                                 default='open',
                                                 copy=False,
                                                 selection=[('open', 'Keep open'), ('reconcile', 'Mark as fully paid')])
    partner_id = fields.Many2one(
        "res.partner", domain="[('is_blocked', '=', False), '|', ('parent_id', '=', False), ('is_company', '=', True), '|', '|', ('customer_state', '=', 'approved'), ('vendor_state', '=', 'approved'), ('internal_approval_state', '=', True)]")
    batch_payment_id = fields.Many2one('batch.payment', ondelete='restrict')

    accounting_approval_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("withdrawn", "Withdrawn"),
        ],
        default="draft", tracking=True, copy=False,
    )
    accounting_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("wait_to_paid", "Waiting to Post"),
            ("paid", "Paid"),
        ], compute="_compute_accounting_state"
    )
    is_accountant_user = fields.Boolean(
        compute='_compute_is_accountant_user')

    analytic_distribution = fields.Json(
        'Analytic Distribution', copy=True, readonly=False)
    report_attachment_id = fields.Many2one('ir.attachment')

    # O2C No. 1: approved (not yet posted) RFPs selected for matching on an inbound payment
    rfp_line_ids = fields.One2many(
        'account.payment.rfp.line', 'payment_id',
        string='Request for Payments', copy=False)
    available_rfp_move_ids = fields.Many2many(
        'account.move', compute='_compute_available_rfp_move_ids')
    rfp_allocated_amount = fields.Monetary(
        string='Allocated to RFPs', compute='_compute_rfp_allocated_amount',
        currency_field='currency_id')

    @api.onchange('due_date')
    def _onchange_due_date(self):
        if self.due_date and not self.invoice_type_id.utility_type:
            self.due_date = get_next_business_day(self.due_date)

    @api.depends_context('uid')
    def _compute_is_accountant_user(self):
        is_accountant_user = self.env.user.has_group(
            'account.group_account_user')
        for record in self:
            record.is_accountant_user = is_accountant_user

    @api.depends("currency_id")
    def _compute_journal_entry_currency_id(self):
        for record in self:
            record.journal_entry_currency_id = record.currency_id

    @api.depends('auto_reconcile_item_ids', 'entry_amount_currency', 'foreign_currency_id',
                 'amount', 'currency_id', 'diff_in_currency_handling')
    def _compute_diff_in_currency(self):
        for payment in self:
            transaction_amount_currency = payment.auto_reconcile_item_ids.mapped(
                'move_id.amount_residual')
            if payment.foreign_currency_id and payment.entry_amount_currency > 0.0:
                payment_amount = payment.entry_amount_currency
            else:
                payment_amount = payment.amount
            payment.diff_in_currency = payment_amount - \
                sum(transaction_amount_currency)

    @api.depends('diff_in_currency', 'auto_reconcile_item_ids')
    def _compute_show_diff_in_currency(self):
        for record in self:
            record.show_diff_in_currency = record.diff_in_currency != 0.0 and record.auto_reconcile_item_ids

    def _compute_amount_in_words(self):
        for record in self:
            if record.currency_id:
                record.amount_in_words_en = record.currency_id.with_context(lang='en_US').amount_to_text(
                    record.amount).capitalize().replace('dong', 'vietnamese dong')
                record.amount_in_words_vn = record.currency_id.with_context(lang='vi_VN').amount_to_text(
                    record.amount).capitalize().replace('dong', 'đồng')
            else:
                record.amount_in_words_vn = False
                record.amount_in_words_en = False

    @api.depends_context('uid')
    @api.depends('state', 'approval_state', 'accounting_approval_state')
    def _compute_approval_readonly(self):
        for rec in self:
            # Accountant is allowed to edit when approval_state is processing and accounting_approval_state is draft
            rec.approval_readonly = (
                rec.state != 'draft' or
                rec.accounting_approval_state != 'draft' or (
                    rec.approval_state != 'draft' and not rec.is_accountant_user
                )
            )

    @api.depends('amount', 'currency_id', 'entry_amount_currency', 'foreign_currency_id')
    def _compute_entry_amount_currency(self):
        for rec in self:
            if rec.foreign_currency_id and not float_is_zero(rec.amount, 2):
                entry_currency_rate = rec.currency_id.round(
                    rec.entry_amount_currency / rec.amount)
            else:
                entry_currency_rate = 1
            rec.entry_currency_rate = entry_currency_rate

    @api.depends('partner_id', 'destination_account_id', 'payment_type',
                 'partner_type', 'currency_id', 'company_currency_id')
    def _compute_available_reconcile_item_ids(self):
        for rec in self:
            filter_domain = rec._get_domain_reconcile_items()
            available_reconcile_item_ids = self.env['account.move.line'].search(
                filter_domain).sorted(lambda x: x.move_id.invoice_date_due)
            rec.available_reconcile_item_ids = available_reconcile_item_ids

    @api.depends('partner_id', 'currency_id', 'company_id', 'payment_type')
    def _compute_available_rfp_move_ids(self):
        AccountMove = self.env['account.move']
        for rec in self:
            if rec.payment_type != 'inbound' or not rec.partner_id:
                rec.available_rfp_move_ids = AccountMove
                continue
            rec.available_rfp_move_ids = AccountMove.search(rec._get_domain_available_rfp_moves())

    @api.depends('rfp_line_ids.amount')
    def _compute_rfp_allocated_amount(self):
        for rec in self:
            rec.rfp_allocated_amount = sum(rec.rfp_line_ids.mapped('amount'))

    def _get_domain_available_rfp_moves(self):
        """RFPs that can be matched with this inbound payment (O2C No. 1).

        Approved RFPs that are not posted yet are included: they are posted
        when the payment is confirmed. Posted RFPs that are not fully paid
        are included as well.
        """
        self.ensure_one()
        return [
            ('company_id', '=', self.company_id.id),
            ('move_type', '=', 'out_invoice'),
            ('is_request_payment', '=', True),
            ('commercial_partner_id', '=', self.partner_id.commercial_partner_id.id),
            ('currency_id', '=', self.currency_id.id),
            '|',
            '&', ('state', '=', 'draft'), ('approval_state', '=', 'approved'),
            '&', ('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')),
        ]

    def _compute_accounting_state(self):
        for record in self:
            accounting_state = 'draft'
            if record.state == "paid":
                accounting_state = 'paid'
            elif record.approval_state == "wait_for_approval":
                accounting_state = 'wait_for_approval'
            elif record.approval_state == 'approved' or not record.is_request_payment:
                accounting_state = 'wait_to_paid'
            record.accounting_state = accounting_state

    @api.onchange('currency_id', 'foreign_currency_id')
    def _onchange_currency_onpayment(self):
        self.ensure_one()
        if self.currency_id.id == self.company_currency_id:
            self.foreign_currency_id = False
            self.entry_amount_currency = 0
        self.auto_reconcile_item_ids = False

    def _get_submit_approval_account_payment_message(self):
        self.ensure_one()
        if self.is_request_payment:
            return "Request for Payment"
        return "Payment"

    def action_post(self):
        self._check_rfp_lines()
        result = super().action_post()
        self._generate_writeoff_journal_entry()
        self._action_auto_reconcile()
        self._post_and_reconcile_rfp_lines()
        return result

    def _check_rfp_lines(self):
        """Validate the RFP allocations before the payment is confirmed (O2C No. 1)."""
        for payment in self.filtered('rfp_line_ids'):
            if payment.payment_type != 'inbound':
                raise UserError(_("RFPs can only be matched with incoming payments."))
            currency = payment.currency_id
            allowed_moves = payment.env['account.move'].search(
                payment._get_domain_available_rfp_moves())
            for line in payment.rfp_line_ids:
                if line.move_id not in allowed_moves:
                    raise UserError(_(
                        "%(rfp)s cannot be matched with this payment. It must belong to the same "
                        "customer and currency, and be approved or posted and not fully paid.",
                        rfp=line.move_id.display_name))
            if currency.compare_amounts(payment.rfp_allocated_amount, payment.amount) > 0:
                raise UserError(_(
                    "The amount allocated to RFPs (%(allocated)s) exceeds the payment amount (%(amount)s).",
                    allocated=formatLang(self.env, payment.rfp_allocated_amount, currency_obj=currency),
                    amount=formatLang(self.env, payment.amount, currency_obj=currency)))
            # Standard reconciliation settles the RFPs in order until the payment is used up,
            # so only the last RFP can be partially paid, and only with the remaining amount.
            lines = payment.rfp_line_ids.sorted(lambda l: (l.sequence, l.id))
            for line in lines:
                is_partial = currency.compare_amounts(line.amount, line.move_amount_open) < 0
                if not is_partial:
                    continue
                is_last = line == lines[-1]
                uses_remaining = currency.compare_amounts(
                    payment.rfp_allocated_amount, payment.amount) == 0
                if not (is_last and uses_remaining):
                    raise UserError(_(
                        "Only the last RFP in the list can be partially paid, and only with the "
                        "remaining amount of the payment (%(rfp)s).",
                        rfp=line.move_id.display_name))

    def _post_and_reconcile_rfp_lines(self):
        """Post the selected approved RFPs and reconcile them with the payment (O2C No. 1).

        The accounting date of each RFP follows the rule of its Request Type
        (``invoice.type.accounting_date_rule``). Posting goes through the normal
        ``_post`` so period closing and posting rights are still enforced.
        """
        for payment in self.filtered(lambda p: p.payment_type == 'inbound' and p.rfp_line_ids):
            if not payment.move_id:
                raise UserError(_(
                    "Payment %s has no journal entry, so the RFPs cannot be reconciled. "
                    "Please set an outstanding receipts account on the payment method.",
                    payment.display_name))
            lines = payment.rfp_line_ids.sorted(lambda l: (l.sequence, l.id))
            draft_rfps = lines.move_id.filtered(lambda m: m.state == 'draft')
            for rfp in draft_rfps:
                accounting_date = (
                    rfp.invoice_type_id._get_rfp_accounting_date(rfp, payment)
                    if rfp.invoice_type_id else payment.date
                )
                rfp.write({'date': accounting_date})
            if draft_rfps:
                draft_rfps._post(soft=False)
                # The accountant confirming the payment stands for the accounting approval.
                draft_rfps.write({'accounting_approval_state': 'approved'})
                for rfp in draft_rfps:
                    rfp.message_post(body=_(
                        "Posted automatically on confirmation of payment %s.",
                        payment.display_name))

            receivable_account = payment.destination_account_id
            payment_lines = payment.move_id.line_ids.filtered(
                lambda l: l.account_id == receivable_account)
            for line in lines:
                rfp_lines = line.move_id.line_ids.filtered(
                    lambda l: l.account_id == receivable_account and not l.reconciled)
                if not rfp_lines:
                    raise UserError(_(
                        "%(rfp)s has no open item on the receivable account %(account)s of the payment.",
                        rfp=line.move_id.display_name, account=receivable_account.display_name))
                open_payment_lines = payment_lines.filtered(lambda l: not l.reconciled)
                if not open_payment_lines:
                    break
                (open_payment_lines + rfp_lines).reconcile()
        return True

    def _action_auto_reconcile(self):
        for rec in self:
            if rec.state != 'paid':
                continue
            auto_reconcile_items = rec.auto_reconcile_item_ids.filtered(
                lambda i: not float_is_zero(i.amount_residual, 2))
            draft_moves = auto_reconcile_items.mapped(
                'move_id').filtered(lambda m: m.state == 'draft')
            draft_moves._post(soft=False)
            if auto_reconcile_items:
                move = rec.move_id
                writeoff_move = rec.move_ids.filtered(
                    lambda x: x.payment_entry_type == 'writeoff')
                if writeoff_move and self.diff_in_currency < 0.0:
                    move += writeoff_move
                auto_reconcile_items += move.line_ids.filtered(
                    lambda line: line.account_id == rec.destination_account_id)
                auto_reconcile_items.reconcile()
        return True

    def action_draft(self):
        self.action_reset_approval()
        self.action_accounting_reset_approval()
        result = super().action_draft()
        self._generate_writeoff_journal_entry()
        return result

    def action_reset_approval(self):
        "Approval State: Rejected | Withdrawn -> Draft"
        self.write({
            "approval_state": "draft",
        })

    def action_accounting_reset_approval(self):
        self.write({
            "accounting_approval_state": "draft"
        })

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        payment_message = self._get_submit_approval_account_payment_message()
        action["context"]["default_name"] = _(
            f"Approval Request for {payment_message} - {self.partner_id.name} ({self.date})"
        )
        return action

    def action_multi_submit_approval(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    _("(%s) Only draft consumption can be submitted for approval", rec.name))

        return super().action_multi_submit_approval()

    def _trigger_action_approve(self):
        for rec in self:
            if (rec.is_request_payment and rec.approval_state == "approved") or not rec.is_request_payment:
                rec.write({"accounting_approval_state": "approved"})

            if rec.is_request_payment and rec.approval_state != "approved":
                rec.write({"approval_state": "approved"})

    def _trigger_action_refuse(self):
        for rec in self:
            if rec.is_request_payment and rec.approval_state != "approved":
                rec.write({"approval_state": "rejected"})

            if (rec.is_request_payment and rec.approval_state == "approved") or not rec.is_request_payment:
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
        for rec in self:
            if rec.state != "draft":
                raise UserError(
                    _(
                        "You cannot submit a request for payment that is not in Draft state."
                    )
                )

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        def _add_readonly_condition(node):
            readonly_condition = "approval_readonly"
            if node.get("readonly"):
                node.set(
                    "readonly",
                    f"({node.attrib.pop('readonly')}) or {readonly_condition}",
                )
            else:
                node.set("readonly", readonly_condition)

        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            nodes = arch.xpath(".//field[not(ancestor::field)]")
            field_attrs = self._fields

            for node in nodes:
                if node.get("name") in ["entry_currency_rate", "approval_readonly", "memo", "date"]:
                    continue
                if field_attrs[node.get("name")].readonly:
                    continue
                _add_readonly_condition(node)

        return arch, view

    def button_open_journal_entry(self):
        res = super().button_open_journal_entry()
        if self.move_ids and len(self.move_ids) >= 2 and isinstance(res, dict):
            res.update({
                'view_mode': 'list,form',
                'res_id': False,
                'domain': [('id', 'in', self.move_ids.ids)]
            })
        return res

    def _remove_writeoff_entry(self):
        writeoff_entries = self.move_ids.filtered(
            lambda x: x.payment_entry_type == 'writeoff')
        for entry in writeoff_entries:
            if entry.state == 'posted':
                entry.button_draft()
            if entry.state == 'draft':
                entry.unlink()

    def _generate_writeoff_journal_entry(self):
        for record in self:
            if record.state != 'paid':
                record._remove_writeoff_entry()
            if (record.state == 'paid' and
                record.writeoff_account_id and
                record.diff_in_currency != 0.0 and
                self.diff_in_currency_handling == 'reconcile' and
                    not record.move_ids.filtered(lambda x: x.payment_entry_type == 'writeoff')):
                move_id = self.env['account.move'].create({
                    'move_type': 'entry',
                    'ref': record.memo,
                    'date': record.date,
                    'journal_id': record.journal_id.id,
                    'company_id': record.company_id.id,
                    'currency_id': record.journal_entry_currency_id.id,
                    'payment_entry_type': 'writeoff',
                    'entry_currency_rate': record.entry_currency_rate,
                    'line_ids': [
                        Command.create(line_vals) for line_vals in record._prepare_move_line_writeoff()
                    ],
                    'origin_payment_id': record.id,
                })
                if move_id:
                    move_id.action_post()

    def _prepare_move_line_writeoff(self):
        diff_in_currency = self.diff_in_currency
        net_off_account = False
        write_off_account = self.writeoff_account_id.id

        if diff_in_currency > 0.0:
            net_off_account = self.outstanding_account_id.id
        else:
            net_off_account = self.destination_account_id.id

        currency_id = self.journal_entry_currency_id.id
        line_vals_list = [
            # Netoff.
            {
                'name': self.writeoff_label,
                'partner_id': self.partner_id.id,
                'amount_currency': diff_in_currency if self.payment_type == 'outbound' else -diff_in_currency,
                'currency_id': currency_id,
                'account_id': net_off_account,
            },
            # Writeoff
            {
                'name': self.writeoff_label,
                'partner_id': self.partner_id.id,
                'amount_currency': -diff_in_currency if self.payment_type == 'outbound' else diff_in_currency,
                'currency_id': currency_id,
                'account_id': write_off_account,
            }
        ]
        return line_vals_list

    def _remove_currencydiff_entry(self):
        currencydiff_entries = self.move_ids.filtered(
            lambda x: x.payment_entry_type == 'currencydiff')
        for entry in currencydiff_entries:
            if entry.state == 'posted':
                entry.button_draft()
            if entry.state == 'draft':
                entry.unlink()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        result = super()._prepare_move_line_default_vals(
            write_off_line_vals, force_balance)
        for res in result:
            line_currency = self.foreign_currency_id or self.currency_id
            res['currency_id'] = line_currency.id
            res['analytic_distribution'] = self.analytic_distribution
            amount = self.amount
            amount_in_currency = self.amount
            if self.currency_id != line_currency:
                amount_in_currency = self.entry_amount_currency
            if self.currency_id != self.company_currency_id:
                amount = self.company_currency_id.round(
                    amount * self.entry_currency_rate)
            if res.get('debit'):
                res['debit'] = amount
                res['amount_currency'] = amount_in_currency
            if res.get('credit'):
                res['credit'] = amount
                res['amount_currency'] = -amount_in_currency
        return result

    def _generate_journal_entry(self, write_off_line_vals=None, force_balance=None, line_ids=None):
        result = super()._generate_journal_entry(
            write_off_line_vals, force_balance, line_ids)
        for rec in self:
            if rec.move_id:
                rec.move_id.write(
                    {'entry_currency_rate': rec.entry_currency_rate,
                     'currency_id': rec.currency_id.id})
        return result

    def action_create_request_payment_report(self):
        self.ensure_one()
        self.with_context(skip_report_generation_check=False)._generate_pdf_report()

    def _generate_pdf_report(self):
        attachments = self.env["ir.attachment"]
        for record in self.filtered(
            lambda r: (
                r.is_request_payment and r.invoice_type_id.report_payment_request_id
            )
        ):
            if (
                record.invoice_type_id.report_payment_request_id.model
                != "account.payment"
            ):
                if self.env.context.get("skip_report_generation_check", True):
                    continue

                raise UserError(
                    _(
                        f"The report payment request from invoice type {record.invoice_type_id.display_name} must be 'account.payment'. Please contact your administrator."
                    )
                )

            request_payment_number = record.request_payment_number
            if not request_payment_number:
                request_sequence = record.invoice_type_id.request_sequence_ids.filtered(
                lambda r: r.company_id == record.company_id)[:1]
                if request_sequence:
                    request_payment_number = request_sequence._next()
                    record.write(
                        {'request_payment_number': request_payment_number})
            report = record.invoice_type_id.report_payment_request_id
            pdf = self.env["ir.actions.report"]._render_qweb_pdf(report, record.id)
            filename = f"{request_payment_number}" + ".pdf"
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

            record.write({'report_attachment_id': report_attachment_id.id})

        return attachments

    def _generate_report_payment_request(self):
        self.ensure_one()
        partner_address = self.partner_id._get_full_address_info()
        vals = {
            'request_payment_number': self.request_payment_number,
            'partner_name_vn': self.partner_id.name,
            'partner_name_en': self.partner_id.name_en,
            'partner_address_vn': partner_address['partner_address_vn'],
            'partner_address_en': partner_address['partner_address_en'],
            'partner_code': self.partner_id.customer_code if self.payment_type == 'inbound' else self.partner_id.vendor_code,
            'vat': self.partner_id.vat,
            'business_type': ', '.join(category.name for category in self.partner_id.category_id),
            'contract_payment_article': self.contract_payment_article,
            'contract_number': self.contract_number,
            'contract_signing_date': format_date(self.env, self.contract_signing_date),
            'amount_in_words_en': self.amount_in_words_en,
            'amount_in_words_vn': self.amount_in_words_vn,
            'amount': formatLang(self.env, self.amount),
            'due_date': format_date(self.env, self.due_date),
            'company_bank_accounts': self.company_id._get_bank_account_info(),
            'date': format_date(self.env, fields.Date.today()),
            'currency': self.currency_id.name,
        }
        return vals

    def _run_auto_update_reconcile_ids(self):
        AccountMoveLine = self.env['account.move.line'].browse()
        for payment in self:
            reconcile_items = AccountMoveLine
            amount_to_reconcile = payment.amount

            for invoice in payment.available_reconcile_item_ids:
                if amount_to_reconcile <= 0.0:
                    break
                if abs(invoice.amount_residual) <= amount_to_reconcile:
                    reconcile_items |= invoice
                    amount_to_reconcile -= abs(invoice.amount_residual)
                else:
                    reconcile_items |= invoice
                    break

            payment.write({'auto_reconcile_item_ids': [
                          (4, item.id) for item in reconcile_items]})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('due_date'):
                is_utility = vals.get('invoice_type_id') and self.env['invoice.type'].browse(vals['invoice_type_id']).utility_type
                if not is_utility:
                    vals['due_date'] = get_next_business_day(vals['due_date'])

        records = super().create(vals_list)

        for record in records:
            if record.is_request_payment and not record.request_payment_number:
                if record.invoice_type_id:
                    request_sequence = record.invoice_type_id.request_sequence_ids.filtered(
                        lambda r: r.company_id == record.company_id
                    )[:1]
                    request_payment_number = request_sequence._next() if request_sequence else None
                else:
                    request_payment_number = self.env['ir.sequence'].with_context(
                        month_sequence=True).sudo().next_by_code('procurement.payment')
                record.write(
                    {'request_payment_number': request_payment_number})

        if 'import_file' in self.env.context:
            records._run_auto_update_reconcile_ids()
        return records

    def write(self, vals):
        if 'due_date' in vals and vals['due_date']:
            if not any(r.invoice_type_id.utility_type for r in self):
                vals['due_date'] = get_next_business_day(vals['due_date'])
        res = super().write(vals)
        if 'move_id' in vals:
            for record in self:
                move_update_vals = {}
                if not record.move_id.invoice_type_id:
                    move_update_vals.update(
                        {'invoice_type_id': record.invoice_type_id.id})
                if not record.move_id.development_phase_id:
                    move_update_vals.update({'development_phase_id': record.development_phase_id.id,
                                             'development_project_id': record.development_project_id.id})
                record.move_id.write(move_update_vals)
        return res

    def action_open_mail_composer(self):
        self.ensure_one()
        template = self._find_mail_template()

        if template and template.model_id.model != "account.payment":
            raise UserError(
                _(
                    f"The default email template from invoice type {self.invoice_type_id.display_name} must be 'account.payment'. Please contact your administrator."
                )
            )

        # Use only the generated report attachment instead of all attachments
        attachment_ids = []
        if self.report_attachment_id:
            attachment_ids = [self.report_attachment_id.id]

        composer_vals = {
            "default_model": "account.payment",
            "default_res_ids": self.ids,
            "default_composition_mode": "comment",
            "default_email_layout_xmlid": "mail.mail_notification_layout_with_responsible_signature",
            "default_template_id": template.id,
            "email_notification_allow_footer": True,
            "default_attachment_ids": [(6, 0, attachment_ids)],
            "force_email": True,
            "default_mail_server_id": self.company_id.invoice_mail_server_id.id
        }

        return {
            'name': 'Send Email',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': composer_vals,
        }

    @api.model
    def _find_mail_template(self):
        return self.invoice_type_id.default_email_template_id or self.env.ref('account.mail_template_data_payment_receipt', raise_if_not_found=False)

    def _get_domain_reconcile_items(self):
        """Get domain for reconcile items."""
        self.ensure_one()
        filter_domain = [
            ('amount_residual', '!=', 0),
            ('partner_id', '=', self.partner_id.id),
            ('currency_id', '=', self.journal_entry_currency_id.id),
            '|', ('move_id.state', '=', 'posted'), ('move_id.accounting_approval_state', '=', 'approved')]

        if self.purchase_order_id:
            filter_domain.append(
                ('move_id', 'in', self.purchase_order_id.invoice_ids.ids))
        elif self.request_purchase_id:
            filter_domain.append(
                ('move_id', 'in', self.request_purchase_id.move_ids.ids))
        else:
            filter_domain.append(
                ('account_id', '=', self.destination_account_id.id))

        if self.payment_type == 'inbound':
            filter_domain.append(('debit', '>', 0))
        else:
            filter_domain.append(('credit', '>', 0))

        if migration_domain_items := self._get_domain_migration_reconcile_items():
            filter_domain = expression.OR([filter_domain, migration_domain_items])

        return filter_domain

    def _get_domain_migration_reconcile_items(self):
        """Get domain for reconcile items of migration moves."""
        self.ensure_one()
        if self.partner_type != 'supplier' or not self.purchase_order_id.date_approve or self.purchase_order_id.date_approve.date() >= date(2026, 2, 28):
            return None

        migration_moves = self.env["account.move"].get_migration_moves(
            move_types=["in_invoice", "in_refund"],
            company_id=self.company_id.id,
            partner_id=self.partner_id.id,
        )
        filter_domain = [('move_id', 'in', migration_moves.ids)]

        if self.payment_type == "inbound":
            filter_domain.append(("debit", ">", 0))
        else:
            filter_domain.append(("credit", ">", 0))

        return filter_domain

    def generate_list_approver_signatures(self):
        self.ensure_one()

        if self.payment_type == "inbound" or (self.accounting_approval_state != "approved" and self.state != "paid"):
            return []

        employee = self.env["hr.employee"].browse()
        request_owner = self._get_request_owner_id() or employee
        accounting_approver = self.env['hr.department'].get_accounting_manager_id(company_id=self.company_id.id) or employee

        final_approver = self._get_final_approver_id()
        final_approver_employee = final_approver._get_employee() if final_approver else employee

        return [
            request_owner.e_signature_file or "",
            accounting_approver.e_signature_file or "",
            final_approver_employee.e_signature_file or "",
        ]
