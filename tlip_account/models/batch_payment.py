from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountRecordPayment(models.Model):
    _name = 'batch.payment'
    _description = 'Batch Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'approval.matrix.mixin']

    name = fields.Char(string='Reference', required=True, default=_('New'))
    date = fields.Date(string='Date', required=True)
    journal_id = fields.Many2one('account.journal', required=True, tracking=True)
    company_id = fields.Many2one(related='journal_id.company_id')
    currency_id = fields.Many2one('res.currency', required=True)

    payment_ids = fields.One2many(
        'account.payment', 'batch_payment_id', string='Payments')
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True, tracking=True)

    total_amount_payment = fields.Monetary(
        string='Total Amount', compute='_compute_total_amount_payment', store=True)
    total_amount_in_words_vn = fields.Char(compute='_compute_amount_in_words')
    total_amount_in_words_en = fields.Char(compute='_compute_amount_in_words')

    available_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        compute='_compute_available_journal_ids'
    )

    @api.depends('payment_ids.amount')
    def _compute_total_amount_payment(self):
        for rec in self:
            rec.total_amount_payment = sum(rec.payment_ids.mapped('amount')) if rec.payment_ids else 0.0

    @api.depends('total_amount_payment', 'currency_id')
    def _compute_amount_in_words(self):
        for rec in self:
            if rec.currency_id:
                rec.total_amount_in_words_en = rec.currency_id.with_context(lang='en_US').amount_to_text(
                    rec.total_amount_payment).capitalize().replace('dong', 'vietnamese dong')
                rec.total_amount_in_words_vn = rec.currency_id.with_context(lang='vi_VN').amount_to_text(
                    rec.total_amount_payment).capitalize().replace('dong', 'đồng')
            else:
                rec.total_amount_in_words_vn = False
                rec.total_amount_in_words_en = False

    @api.depends('payment_type')
    def _compute_available_journal_ids(self):
        """
        Get all journals having at least one payment method for inbound/outbound depending on the payment_type.
        """
        journals = self.env['account.journal'].search([
            '|',
            ('company_id', 'parent_of', self.env.company.id),
            ('company_id', 'child_of', self.env.company.id),
            ('type', 'in', ('bank', 'cash', 'credit')),
        ])
        for pay in self:
            if pay.payment_type == 'inbound':
                pay.available_journal_ids = journals.filtered('inbound_payment_method_line_ids')
            else:
                pay.available_journal_ids = journals.filtered('outbound_payment_method_line_ids')

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        self.payment_ids.write({'payment_type': self.payment_type})

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.payment_ids:
            self.payment_ids.write({'journal_id': self.journal_id.id})

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action["context"]["default_name"] = _(
            f"Approval Request for Batch Payment {self.name} - {self.payment_type}"
        )
        return action

    def _trigger_action_after_submit(self, request):
        res = super()._trigger_action_after_submit(request=request)
        self.write({'approval_state': 'wait_for_approval'})
        self.payment_ids.write({'approval_state': 'wait_for_approval'})
        return res

    def _trigger_action_approve(self):
        res = super()._trigger_action_approve()
        self.write({'approval_state': 'approved'})
        self.payment_ids.write({'approval_state': 'approved'})
        self.payment_ids.filtered(lambda pay: pay.state in {
                                  False, 'draft', 'in_process'}).action_post()
        return res

    def _trigger_action_withdraw(self, reason: str):
        res = super()._trigger_action_withdraw(reason)
        self.write({'approval_state': 'withdrawn'})
        self.payment_ids.write({'approval_state': 'withdrawn'})
        return res

    def _validate_submit_approval(self):
        self.ensure_one()
        if not self.payment_ids:
            raise UserError(_('Please add at least one payment.'))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            sequence_code = 'batch.payment.outbound' if vals['payment_type'] == 'outbound' else 'batch.payment.outbound'
            vals['name'] = self.env['ir.sequence'].with_context(month_sequence=True).sudo().next_by_code(sequence_code) or '/'
        return super().create(vals)
