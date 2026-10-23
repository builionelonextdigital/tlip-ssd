from datetime import datetime, timedelta
import logging

from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.tools import groupby, float_is_zero
from odoo.tools.date_utils import end_of
from odoo.tools import groupby, float_is_zero
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ElectricityConsumption(models.Model):
    _name = "electricity.consumption"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'approval.matrix.mixin']
    _description = "Electricity Consumption"
    _order = 'id desc'

    name = fields.Char("Reference", tracking=True)
    electricity_point_id = fields.Many2one(
        'electricity.point', 'Electricity Point', tracking=True, required=True, readonly=False)
    electricity_type = fields.Selection(related='electricity_point_id.electricity_type')
    partner_id = fields.Many2one(
        'res.partner', 'Customer', tracking=True,
        compute='_compute_partner_id', store=True, readonly=True)
    record_date = fields.Date(
        'Recorded Date', tracking=True, required=True, readonly=False)
    date_from = fields.Date(tracking=True, required=True, readonly=False)
    date_to = fields.Date(tracking=True, required=True, readonly=False)
    invoice_due_date = fields.Date(tracking=True, required=True, readonly=False)
    kfactor = fields.Float('K-factor', tracking=True, readonly=False)
    cosphi = fields.Float('Cosphi', tracking=True, readonly=False)
    reative_power_quantity = fields.Float('Reative Power Quantity')
    electricity_connection_charge = fields.Monetary('Electricity Connection Charges', tracking=True, readonly=False)
    connection_rate = fields.Float(string='Connection Rate', tracking=True, readonly=False)
    currency_id = fields.Many2one(
        'res.currency', tracking=True, required=True, readonly=False,
        default=lambda self: self.env.company.currency_id)
    line_ids = fields.One2many(
        'electricity.consumption.line', 'consumption_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wait_for_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),], string='State', default='draft', tracking=True, required=True)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)
    invoice_ids = fields.One2many(
        'account.move', 'electricity_consumption_id', string='Invoice')
    source = fields.Selection([('manual', 'Manual'),
                               ('power_app', 'Power App')], default='manual')
    total_amount = fields.Monetary(compute='_compute_total')
    total_quantity = fields.Float(compute='_compute_total')
    total_reactive_power = fields.Float(compute='_compute_total')
    total_connection_charge = fields.Monetary(compute='_compute_total')

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
            record.total_reactive_power = record.reative_power_quantity
            record.total_connection_charge = record.electricity_connection_charge

    @api.depends('electricity_point_id')
    def _compute_partner_id(self):
        for rec in self:
            rec.partner_id = rec.electricity_point_id.partner_id

    @api.onchange('cosphi')
    def _onchange_cosphi(self):
        self.kfactor = self.env['electricity.kfactor']._get_kfactor(
            self.cosphi)

    @api.onchange('total_amount', 'connection_rate')
    def _onchange_consumption_line(self):
        # Use onchange to recalculate the connection charge when user updates on UI.
        # Avoid rewrite conflict with _generate_electricity_consumption
        self.electricity_connection_charge = self.connection_rate * self.total_amount

    def action_submit_approval(self):
        self._validate_submit_approval()
        # 8/12/2025 Auto approve when submit electricity consumption
        self._trigger_action_approve()
        return self.action_view_request_payment()

    def action_reset(self):
        self.write({
            'state': 'draft',
        })

    def _prepare_invoice_line_vals(self, **kwargs):
        self.ensure_one()
        vals = []
        lines = self.line_ids.filtered(lambda l: not l.is_reactive_power_line)
        index = 1
        for line in lines:
            multiplier = line.multiplier
            if float_is_zero(multiplier, 2):
                multiplier = 1.0            
            vals += [(0, 0, {
                'last_value': line.start_meter_reading,
                'new_value': line.end_meter_reading,
                'multiplier': multiplier,
                'utility_quantity': line.quantity + line.modify_quantity,
                'quantity': line.quantity + line.modify_quantity,
                'price_unit': line.unit_price,
                'product_id': line.product_id.id,
                'analytic_distribution': line.analytic_distribution,
                'date_maturity': self.invoice_due_date,
                'tax_ids': [(4, line.tax_id.id)] if line.tax_id else False,
                'name': line.name,
                'line_no': index 
            })]
            index += 1
        return vals

    def _prepare_connection_invoice_line_vals(self, **kwargs):
        self.ensure_one()
        
        product = self.company_id.power_connection_product_id
        tax = product.product_tmpl_id._get_tax(self.company_id, self.electricity_point_id.tax_apply_type)
        analytic_account = product.income_budget_code_id._get_analytic_account(self.company_id.id) if product.income_budget_code_id else False
        vals = [(0, 0, {
            'connection_quantity': self.total_amount,
            'connection_rate': self.connection_rate,
            'quantity': 1,
            'price_unit': self.total_amount * self.connection_rate / 100,
            'product_id': product.id,
            'date_maturity': self.invoice_due_date,
            'analytic_distribution': {analytic_account.id: 100} if analytic_account else {},
            'tax_ids': [(4, tax.id)] if tax else False,
            'line_no': 1 
        })]
        return vals

    def _prepare_reactive_invoice_line_vals(self):
        lines = self.line_ids.filtered(lambda l: not l.is_reactive_power_line)
        unit_price = (sum(lines.mapped('amount')) * self.kfactor) / 100
        line = self.line_ids[:1]

        product = self.company_id.reactive_power_product_id
        tax = product.product_tmpl_id._get_tax(self.company_id, self.electricity_point_id.tax_apply_type)
        analytic_account = product.income_budget_code_id._get_analytic_account(self.company_id.id) if product.income_budget_code_id else False

        return [(0, 0, {
            'radio_cosfi': self.cosphi,
            'radio_kfactor': self.kfactor,
            'product_id': product.id,
            'price_unit': unit_price,
            'analytic_distribution': {analytic_account.id: 100} if analytic_account else {},
            'date_maturity': self.invoice_due_date,
            'tax_ids': [(4, tax.id)] if tax else False,
            'name': f"{product.invoice_description_vn} ({product.invoice_description_en})",
            'line_no': 1 
        })]

    def _prepare_invoice_vals(self, **kwargs):
        self.ensure_one()
        utility_lines = []
        contract_number = self.electricity_point_id.contract_number
        contract_payment_article = self.electricity_point_id.contract_payment_article
        contract_signing_date = self.electricity_point_id.signing_date
        if kwargs['utility_electricity_type'] == 'consumption':
            line_vals = self._prepare_invoice_line_vals()
            ref = f"{self.name} - Consumption"
        elif kwargs['utility_electricity_type'] == 'connection_charge':
            line_vals = self._prepare_connection_invoice_line_vals()
            ref = f"{self.name} - Connection Charge"
            contract_number = self.electricity_point_id.connection_contract_number
            contract_payment_article = self.electricity_point_id.connection_contract_payment_article
            contract_signing_date = self.electricity_point_id.connection_signing_date
        else:
            line_vals = self._prepare_reactive_invoice_line_vals()
            utility_lines = [(0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.quantity + line.modify_quantity,
                'unit_price': line.unit_price,
                'amount': line.amount
            }) for line in self.line_ids]
            ref = f"{self.name} - Reactive Power"

        res = {
            "name": "/",
            "contract_number": contract_number,
            'contract_payment_article': contract_payment_article,
            "contract_signing_date": contract_signing_date,
            "metering_point": self.electricity_point_id.electricity_point_name or self.electricity_point_id.name,
            "journal_id": self.company_id.electrict_journal_id.id,
            "partner_id": self.partner_id.id,
            "move_type": "out_invoice",
            "invoice_line_ids": line_vals,
            "electricity_consumption_id": self.id,
            'utitlity_period_from': self.date_from,
            'utitlity_period_to': self.date_to,
            "currency_id": self.currency_id.id,
            "company_id": self.company_id.id,
            'utility_line_ids': utility_lines,
            'is_request_payment': True,
            'user_id': self.env.user.id,
            'partner_shipping_id': self.electricity_point_id.invoice_address_id.id or self.partner_id.id,
            'ref': ref,
            'customer_contact_ids': [(6, 0, self.electricity_point_id.customer_contact_ids.ids)],
            'invoice_date_due': self.invoice_due_date,
            'invoice_date': self.date_to,
            'date': self.date_to,
            'email_for_payment': self.electricity_point_id.email_for_payment,
            'email_for_invoice': self.electricity_point_id.email_for_invoice,
            'entry_currency_rate': self.line_ids[0].exchange_rate if (self.line_ids and self.line_ids[0].exchange_rate > 0) else 1,
            'electricity_point_id': self.electricity_point_id.id,
            **kwargs
        }
        return res

    def _create_invoice(self, active=True):
        invoices = []
        for record in self.filtered(lambda r: not r.invoice_ids):
            invoice_type = record.company_id.electrict_consumption_invoice_type_id
            sequence = invoice_type.request_sequence_ids.filtered(
                lambda r: r.company_id == record.company_id)[:1]
            request_number = False
            if sequence:
                request_number = sequence.next_by_id()
            invoices += [record._prepare_invoice_vals(
                **{"utility_electricity_type": "consumption", 'invoice_type_id': invoice_type.id, 'request_payment_number': request_number})]

            if record.kfactor > 0:
                invoice_type = record.company_id.electrict_reactive_power_invoice_type_id
                sequence = invoice_type.request_sequence_ids.filtered(
                    lambda r: r.company_id == record.company_id)[:1]
                request_number = False
                if sequence:
                    request_number = sequence.next_by_id()
                invoices += [record._prepare_invoice_vals(
                    **{"utility_electricity_type": "reactive_power", 'invoice_type_id': invoice_type.id, 'request_payment_number': request_number})]
                
            if record.connection_rate > 0:
                invoice_type = record.company_id.electrict_connection_invoice_type_id
                sequence = invoice_type.request_sequence_ids.filtered(
                    lambda r: r.company_id == record.company_id)[:1]
                request_number = False
                if sequence:
                    request_number = sequence.next_by_id()
                invoices += [record._prepare_invoice_vals(
                    **{"utility_electricity_type": "connection_charge", 'invoice_type_id': invoice_type.id, 'request_payment_number': request_number})]
                
        invoices = self.env['account.move'].create(invoices)
        return invoices

    def _trigger_action_approve(self):
        try:
            self.write({'state': 'approved'})
            invoices = self.with_context(active_test=False).mapped('invoice_ids').filtered(lambda r: r.state == 'draft')
            if not invoices:
                invoices = self.sudo()._create_invoice(active=True)
                invoices._generate_pdf_report()

            invoices.sudo().write({'active': True})
            invoices._compute_minvoice_data()
        except Exception as e:
            self.message_post(body=_("Auto approve failed: %s" % e))
            _logger.error("Failed to auto approve electricity consumption %s: %s", self.id, e)

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _auto_confirm(self):
        self.ensure_one()
        if self.electricity_point_id.auto_issue_payment:
            self._trigger_action_approve()
        else:
            base_date = fields.Datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0)

            from_hours = int(self.company_id.consumption_from)
            from_minutes = int(
                (self.company_id.consumption_from - from_hours) * 60)
            from_time = base_date + \
                timedelta(hours=from_hours, minutes=from_minutes)

            to_hours = int(self.company_id.consumption_to)
            to_minutes = int((self.company_id.consumption_to - to_hours) * 60)
            to_time = base_date + timedelta(hours=to_hours, minutes=to_minutes)
            if from_time <= self.create_date and self.create_date <= to_time and self.create_date.date() == end_of(self.create_date.date(), 'month'):
                self._trigger_action_approve()

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
        self.sudo().with_context(active_test=False).invoice_ids.unlink()
        invoices = self.sudo()._create_invoice(active=True)
        for invoice in invoices:
            invoice.with_context(active_test=False, generate_pdf_report=True)._generate_pdf_report()
        invoices.write({'active': False})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'electricity.consumption.sequence')
        rec = super(ElectricityConsumption, self).create(vals)
        rec._auto_confirm()
        return rec

    def unlink(self):
        inactive_invoices = self.filtered(lambda r: r.state == 'draft').mapped('invoice_ids')
        inactive_invoices.unlink()
        if any(record.invoice_ids for record in self) and 'force_delete' not in self.env.context:
            raise ValidationError(
                _("Do not allow to remove consumption data after generating invoice"))
        return super().unlink()


class ElectricityConsumptionLine(models.Model):
    _name = "electricity.consumption.line"
    _inherit = "analytic.mixin"
    _description = "Electricity Consumption Line"

    consumption_id = fields.Many2one(
        'electricity.consumption', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Time of Use Period',
        domain="[('utility_type', '=', 'electricity')]", required=True)
    start_meter_reading = fields.Float('Start Meter Reading', required=True)
    end_meter_reading = fields.Float('End Meter Reading', required=True)
    multiplier = fields.Float('Multiplier', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id')
    currency_id = fields.Many2one(
        'res.currency', related='consumption_id.currency_id')
    exchange_rate = fields.Float()
    quantity = fields.Float('Quantity', required=True)
    modify_quantity = fields.Float('+/- Quantity')
    unit_price = fields.Float(
        string='Unit Price')
    tax_id = fields.Many2one('account.tax', string='Tax',
                             compute='_compute_tax_id', store=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    company_id = fields.Many2one(
        'res.company', related='consumption_id.company_id')
    is_reactive_power_line = fields.Boolean()
    name = fields.Text(string='Description', compute='_compute_name', store=True, readonly=False)
    analytic_distribution = fields.Json(string="Budget Code", compute='_compute_analytic_distribution', store=True)

    @api.constrains('start_meter_reading', 'end_meter_reading')
    def _check_meter_reading(self):
        for rec in self:
            if rec.start_meter_reading > rec.end_meter_reading:
                raise ValidationError(_("Start meter reading should be less than end meter reading."))

    @api.depends('product_id')
    def _compute_name(self):
        for rec in self:
            name = rec.name
            if rec.product_id.invoice_description_vn and rec.product_id.invoice_description_en:
                name = f"{rec.product_id.invoice_description_vn} ({rec.product_id.invoice_description_en})"
            rec.name = name

    @api.onchange('end_meter_reading', 'start_meter_reading', 'multiplier')
    def _onchange_quantity(self):
        self.quantity = (self.end_meter_reading - self.start_meter_reading) * self.multiplier

    @api.depends_context('company')
    @api.depends('product_id', 'company_id', 'consumption_id.electricity_point_id.tax_apply_type')
    def _compute_tax_id(self):
        for record in self:
            if record.consumption_id.electricity_point_id.tax_apply_type == 'non_epe':
                record.tax_id = record.product_id.taxes_id.filtered(
                    lambda r: r.company_id == record.company_id)[:1]
            else:
                record.tax_id = record.product_id.epe_taxes_id.filtered(
                    lambda r: r.company_id == record.company_id)[:1]

    @api.onchange('quantity', 'modify_quantity', 'unit_price', 'multiplier')
    def _onchange_amount(self):
        self.amount = (self.quantity + self.modify_quantity) * self.unit_price
    
    @api.depends('product_id', 'consumption_id.electricity_point_id')
    def _compute_analytic_distribution(self):
        for record in self:
            pricelist = record.consumption_id.electricity_point_id.pricelist_id
            pricelist_line = pricelist.pricelist_item_ids.filtered(lambda l: l.product_id == record.product_id)
            if record.product_id and pricelist_line:
                analytic_account = self.env['account.analytic.account']._get_analytic_account_id(pricelist_line[0].budget_code_id, record.consumption_id.company_id.id)
                analytic_distribution = {analytic_account.id: 100}
                record.analytic_distribution = analytic_distribution
            else:
                if record.product_id:
                    analytic_account = self.env['account.analytic.account']._get_analytic_account_id(record.product_id.income_budget_code_id, record.consumption_id.company_id.id)
                    analytic_distribution = {analytic_account.id: 100}
                else:
                    analytic_distribution = {}
                record.analytic_distribution = analytic_distribution


    @api.onchange('product_id', 'consumption_id')
    def _onchange_product(self):
        pricelist = self.consumption_id.electricity_point_id.pricelist_id
        pricelist_line = pricelist.pricelist_item_ids.filtered(lambda l: l.product_id == self.product_id)
        if self.product_id and pricelist_line:
            self.unit_price = pricelist_line[0].unit_price
        else:
            self.unit_price = self.product_id.list_price
