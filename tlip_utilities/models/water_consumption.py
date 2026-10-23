from dateutil.relativedelta import relativedelta
import logging
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WaterConsumption(models.Model):
    _name = "water.consumption"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'approval.matrix.mixin']
    _description = "Water Consumption"
    _order = 'id desc'

    name = fields.Char("Reference", tracking=True)
    partner_id = fields.Many2one(
        'res.partner', 'Customer', tracking=True,
        compute='_compute_partner_id', store=True, readonly=True)
    partner_code = fields.Char(
        'Customer Code', related='partner_id.customer_code')
    water_point_id = fields.Many2one(
        'water.point', 'Water Point', tracking=True, required=True, readonly=False)
    record_date = fields.Date(
        'Recorded Date', tracking=True, required=True, readonly=False)
    date_from = fields.Date(tracking=True, required=True, readonly=False)
    date_to = fields.Date(tracking=True, required=True, readonly=False)
    invoice_due_date = fields.Date(tracking=True, required=True, readonly=False)
    currency_id = fields.Many2one(
        'res.currency', tracking=True, required=True, readonly=False)
    line_ids = fields.One2many(
        'water.consumption.line', 'consumption_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wait_for_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),], string='State', default='draft', tracking=True, required=True)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    invoice_ids = fields.One2many(
        'account.move', 'water_consumption_id', string='Invoice')
    total_amount = fields.Monetary(compute='_compute_total')
    total_quantity = fields.Float(compute='_compute_total')
    source = fields.Selection([('manual', 'Manual'),
                               ('water_app', 'Power App')], default='manual')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if any(record.date_from > record.date_to for record in self):
            raise ValidationError(_("Start date should precede the end date."))

    @api.depends('line_ids.amount', 'line_ids.quantity', 'line_ids.modify_quantity')
    def _compute_total(self):
        for record in self:
            record.total_amount = sum(record.mapped('line_ids.amount'))
            record.total_quantity = sum(record.mapped(
                'line_ids.quantity')) + sum(record.mapped('line_ids.modify_quantity'))

    @api.depends('water_point_id')
    def _compute_partner_id(self):
        for rec in self:
            rec.partner_id = rec.water_point_id.partner_id

    def action_submit_approval(self):
        self._validate_submit_approval()
        # 8/12/2025 Auto approve when submit electricity consumption
        self._trigger_action_approve()
        return self.action_view_request_payment()

    def action_reset(self):
        self.write({
            'state': 'draft',
        })

    def _prepare_invoice_line_vals(self):
        self.ensure_one()
        vals = []
        index = 1
        for line in self.line_ids:
            vals += [(0, 0, {
                'last_value': line.start_value,
                'new_value': line.end_value,
                'utility_quantity': line.quantity + line.modify_quantity,
                'quantity': line.quantity + line.modify_quantity,
                'price_unit': line.unit_price,
                'analytic_distribution': line.analytic_distribution,
                'product_id': line.product_id.id,
                'date_maturity': self.invoice_due_date,
                'tax_ids': [(4, line.tax_id.id)] if line.tax_id else False,
                'name': line.name,
                'line_no': index 
            })]
            index += 1
        return vals

    def _prepare_invoice_vals(self, **kwargs):
        self.ensure_one()
        line_vals = self._prepare_invoice_line_vals()
        res = {
            "name": "/",
            "contract_number": self.water_point_id.contract_number,
            'contract_payment_article': self.water_point_id.contract_payment_article,
            "contract_signing_date": self.water_point_id.signing_date,
            "metering_point": self.water_point_id.name,
            "journal_id": self.company_id.water_journal_id.id,
            "partner_id": self.water_point_id.partner_id.id,
            "move_type": "out_invoice",
            "invoice_line_ids": line_vals,
            "currency_id": self.currency_id.id,
            "water_consumption_id": self.id,
            'utitlity_period_from': self.date_from,
            'utitlity_period_to': self.date_to,
            "company_id": self.company_id.id,
            "utility_type": 'water',
            'user_id': self.env.user.id,
            'invoice_type_id': self.company_id.water_consumption_invoice_type_id.id,
            'is_request_payment': True,
            'partner_shipping_id': self.water_point_id.invoice_address_id.id or self.partner_id.id,
            'customer_contact_ids': [(6, 0, self.water_point_id.customer_contact_ids.ids)],
            'invoice_date_due': self.invoice_due_date,
            'invoice_date': self.date_to,
            'date': self.date_to,
            'ref': self.name,
            'email_for_payment': self.water_point_id.email_for_payment,
            'email_for_invoice': self.water_point_id.email_for_invoice,
            'entry_currency_rate': self.line_ids[0].exchange_rate if (self.line_ids and self.line_ids[0].exchange_rate > 0) else 1,
            'water_point_id': self.water_point_id.id,
            **kwargs
        }
        return res

    def _create_invoice(self, active=True):
        invoices = []
        for record in self.filtered(lambda r: not r.invoice_ids):
            invoices += [record._prepare_invoice_vals()]
        invoices = self.env['account.move'].create(invoices)
        return invoices

    def _trigger_action_approve(self):
        try:
            self.write({'state': 'approved'})
            invoices = self.with_context(active_test=False).mapped('invoice_ids').filtered(lambda r: r.state == 'draft')
            if not invoices:
                invoices = self.sudo()._create_invoice(active=True)
                invoices._generate_pdf_report()
        except Exception as e:
            self.message_post(body=_("Auto approve failed: %s" % e))
            _logger.error("Failed to auto approve water consumption %s: %s", self.id, e)

        invoices.sudo().write({'active': True})
        invoices._compute_minvoice_data()
    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _validate_submit_approval(self):
        if not self.line_ids:
            raise ValidationError(_("Please add consumption lines."))
        if self.state != 'draft':
            raise ValidationError(
                _("(%s) Only draft consumption can be submitted for approval", self.name))

    def action_view_request_payment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "tlip_utilities.action_request_payment_view")
        action["domain"] = [("id", "in", self.invoice_ids.ids)]
        return action

    def action_create_request_payment(self):
        self.ensure_one()
        self.sudo().invoice_ids.unlink()
        invoices = self.sudo()._create_invoice(active=True)
        for invoice in invoices:
            invoice.with_context(active_test=False, generate_pdf_report=True)._generate_pdf_report()
        invoices.write({'active': False})

    def _auto_confirm(self):
        self.ensure_one()
        if self.water_point_id.auto_issue_payment:
            self._trigger_action_approve()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'water.consumption.sequence')
        rec = super(WaterConsumption, self).create(vals)
        rec._auto_confirm()
        return rec

    def unlink(self):
        inactive_invoices = self.filtered(lambda r: r.state == 'draft').mapped('invoice_ids')
        inactive_invoices.unlink()
        if any(record.invoice_ids for record in self) and 'force_delete' not in self.env.context:
            raise ValidationError(
                _("Do not allow to remove consumption data after generating invoice"))
        return super().unlink()


class WaterConsumptionLine(models.Model):
    _name = "water.consumption.line"
    _inherit = "analytic.mixin"
    _description = "Water Consumption Line"

    consumption_id = fields.Many2one(
        'water.consumption', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Fee',
        domain="[('utility_type', '=', 'water')]", required=True)
    start_value = fields.Float('Start Value', required=True)
    end_value = fields.Float('End Value', required=True)
    uom_id = fields.Many2one(
        'uom.uom', related='product_id.uom_id', store=True)
    currency_id = fields.Many2one(
        'res.currency', related='consumption_id.currency_id')
    exchange_rate = fields.Float()
    quantity = fields.Float('Quantity', required=True)
    modify_quantity = fields.Float('+/- Quantity')
    unit_price = fields.Float(string='Unit Price')
    vat = fields.Monetary(
        string='VAT Amount', currency_field='currency_id')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    tax_id = fields.Many2one('account.tax', string='Tax',
                             compute='_compute_tax_id', store=True)
    company_id = fields.Many2one(
        'res.company', related='consumption_id.company_id')
    name = fields.Text(string='Description', compute='_compute_name', store=True, readonly=False)
    analytic_distribution = fields.Json(string="Budget Code", compute='_compute_analytic_distribution', store=True)

    @api.constrains('start_value', 'end_value')
    def _check_values(self):
        if any(record.start_value > record.end_value for record in self):
            raise ValidationError(_("Start value should precede the end value."))

    @api.depends('product_id')
    def _compute_name(self):
        for rec in self:
            name = rec.name
            if rec.product_id.invoice_description_vn and rec.product_id.invoice_description_en:
                name = f"{rec.product_id.invoice_description_vn} ({rec.product_id.invoice_description_en})"
            rec.name = name

    @api.onchange('start_value', 'end_value')
    def _onchange_quantity(self):
        self.quantity = self.end_value - self.start_value

    @api.depends_context('company')
    @api.depends('product_id', 'company_id', 'consumption_id.water_point_id.tax_apply_type')
    def _compute_tax_id(self):
        for record in self:
            if record.consumption_id.water_point_id.tax_apply_type == 'non_epe':
                record.tax_id = record.product_id.taxes_id.filtered(
                    lambda r: r.company_id == record.company_id)[:1]
            else:
                record.tax_id = record.product_id.epe_taxes_id.filtered(
                    lambda r: r.company_id == record.company_id)[:1]
                
    @api.depends('product_id', 'consumption_id.water_point_id')
    def _compute_analytic_distribution(self):
        for record in self:
            pricelist = record.consumption_id.water_point_id.pricelist_id
            pricelist_line = pricelist.pricelist_item_ids.filtered(lambda l: l.product_id == record.product_id)
            if record.product_id and pricelist_line:
                analytic_account = self.env['account.analytic.account']._get_analytic_account_id(pricelist_line[0].budget_code_id, self.consumption_id.company_id.id)
                analytic_distribution = {analytic_account.id: 100}
                record.analytic_distribution = analytic_distribution
            else:
                if record.product_id:
                    analytic_account = self.env['account.analytic.account']._get_analytic_account_id(record.product_id.income_budget_code_id, self.consumption_id.company_id.id)
                    analytic_distribution = {analytic_account.id: 100}
                else:
                    analytic_distribution = {}
                record.analytic_distribution = analytic_distribution

    @api.onchange('quantity', 'modify_quantity', 'unit_price')
    def _onchange_amount(self):
        self.amount = (self.quantity + self.modify_quantity) * self.unit_price

    @api.onchange('product_id')
    def _onchange_product(self):
        pricelist = self.consumption_id.water_point_id.pricelist_id
        pricelist_line = pricelist.pricelist_item_ids.filtered(lambda l: l.product_id == self.product_id)
        if self.product_id and pricelist_line:
            self.unit_price = pricelist_line[0].unit_price
        else:
            self.unit_price = self.product_id.list_price
