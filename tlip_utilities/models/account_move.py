from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import format_date, formatLang


class AccountMove(models.Model):
    _inherit = "account.move"

    utility_type = fields.Selection(
        [('electricity', 'Electricity'),
         ('water', 'Water')], string="Utility Type", compute='_compute_utility_type', store=True)
    utility_electricity_type = fields.Selection(selection=[
        ('consumption', 'Consumption'),
        ('reactive_power', 'Reactive Power'),
        ('connection_charge', 'Connection Charge')
    ], compute='_compute_utility_electricity_type', store=True)
    utility_quantity_based_on = fields.Selection(related='invoice_type_id.utility_quantity_based_on')
    utility_line_ids = fields.One2many(
        'invoice.utility.consumption.line', 'move_id', 'Utility Lines')
    utility_total_amount = fields.Float(
        compute='_compute_utility_total_amount', store=True)
    electricity_consumption_id = fields.Many2one('electricity.consumption', copy=False)
    water_consumption_id = fields.Many2one('water.consumption', copy=False)
    active = fields.Boolean(default=True)
    utitlity_period_from = fields.Date()
    utitlity_period_to = fields.Date()

    electricity_point_id = fields.Many2one('electricity.point', ondelete='restrict')
    water_point_id = fields.Many2one('water.point', ondelete='restrict')
    measurement_point_location_name = fields.Char(
        string="Measurement Point Location Name",
        related='water_point_id.measurement_point_location_name',
        store=False,
        readonly=True
    )
    electricity_type = fields.Selection(related='electricity_point_id.electricity_type')

    @api.onchange('electricity_point_id', 'water_point_id')
    def _onchange_metering_point(self):
        metering_point = False
        is_connection_charge = False
        if self.utility_type == 'electricity':
            metering_point =  self.electricity_point_id
            is_connection_charge = self.invoice_type_id.utility_electricity_type == 'connection_charge'
        elif self.utility_type == 'water':
            metering_point =  self.water_point_id
        else:
            self.electricity_point_id = False
            self.water_point_id = False

        if is_connection_charge:
            self.contract_number = metering_point.connection_contract_number
            self.contract_payment_article = metering_point.connection_contract_payment_article
            self.contract_signing_date = metering_point.connection_signing_date
        elif metering_point:
            self.contract_number = metering_point.contract_number
            self.contract_payment_article = metering_point.contract_payment_article
            self.contract_signing_date = metering_point.signing_date
            self.metering_point = metering_point.name

    @api.onchange('utitlity_period_from', 'utitlity_period_to', 'invoice_type_id')
    def _onchange_utility_period_to(self):
        # Since UI using utitlity_period_from with widget date range, so we need to include utility_period_from in the onchange to make sure the onchange is triggered when user change the date range
        if self.utitlity_period_to and self.invoice_type_id.type == 'utility':
            if self.invoice_date > self.utitlity_period_to:
                self.invoice_date = self.utitlity_period_to
            if self.date > self.utitlity_period_to:
                self.date = self.utitlity_period_to
            if self.invoice_date_due > self.utitlity_period_to:
                self.invoice_date_due = self.utitlity_period_to

    def _trigger_action_approve(self):
        super()._trigger_action_approve()
        if 'approved' in (self.approval_state, self.accounting_approval_state) and self.invoice_type_id.type == 'utility':
            self.sudo().with_context(force_post=True).action_post()
            self.with_delay().publish_minvoices(self, action='publish')

    def _email_subject_invoice_type(self):
        if self.utility_type == 'electricity':
            if self.utility_electricity_type == 'consumption':
                return f'Yêu cầu thanh toán {self.request_payment_number} - Tiền điện chốt ngày {format_date(self.env, self.electricity_consumption_id.record_date)}'
            elif self.utility_electricity_type == 'reactive_power':
                return f'Yêu cầu thanh toán {self.request_payment_number} - Tiền công suất phản kháng chốt ngày {format_date(self.env, self.electricity_consumption_id.record_date)}'
            else:
                return f'Yêu cầu thanh toán {self.request_payment_number} - Phí đấu nối điện chốt ngày {format_date(self.env, self.electricity_consumption_id.record_date)}'
        elif self.utility_type == 'water':
            return f'Yêu cầu thanh toán {self.request_payment_number} - Phí nước chốt ngày {format_date(self.env, self.water_consumption_id.record_date)}'
        return super()._email_subject_invoice_type()

    @api.depends('invoice_type_id')
    def _compute_utility_type(self):
        for record in self:
            record.utility_type = record.invoice_type_id.utility_type

    @api.depends('invoice_type_id')
    def _compute_utility_electricity_type(self):
        for record in self:
            record.utility_electricity_type = record.invoice_type_id.utility_electricity_type

    @api.depends('utility_line_ids', 'utility_line_ids.amount')
    def _compute_utility_total_amount(self):
        for rec in self:
            rec.utility_total_amount = sum(
                [utility_line.amount for utility_line in rec.utility_line_ids])

    def _generate_report_payment_request(self):
        vals = super()._generate_report_payment_request()
        if self.utility_electricity_type == "reactive_power" and len(self.utility_line_ids) < 3:
            raise UserError(_('Reactive Electricity Consumption lines are less than 3 lines, cannot generate report.'))

        consumption_rec = self.electricity_consumption_id or self.water_consumption_id
        vals.update({
            'utitlity_period_from': format_date(self.env, self.utitlity_period_from),
            'utitlity_period_to': format_date(self.env, self.utitlity_period_to),
            'reative_power_quantity': formatLang(self.env, consumption_rec.reative_power_quantity, digits=2) if consumption_rec._name == 'electricity.consumption' else 0.0,
            'electric_consumption': [{
                'name': line.product_id.name,
                'quantity': formatLang(self.env, line.quantity, digits=0),
                'amount': formatLang(self.env, line.amount, digits=0),
            } for line in self.utility_line_ids],
        })
        return vals

    def _generate_pdf_report(self):
        attachments = super()._generate_pdf_report()
        for attachment in attachments:
            record = self.filtered(lambda r: r.id == attachment.res_id)
            if record.electricity_consumption_id:
                new_attachment = attachment.copy(
                    {'res_model': 'electricity.consumption', 'res_id': record.electricity_consumption_id.id})
            elif record.water_consumption_id:
                new_attachment = attachment.copy(
                    {'res_model': 'water.consumption', 'res_id': record.water_consumption_id.id})
        return attachments

    @api.model
    def create(self, vals):
        if vals.get('utitlity_period_to') and not vals.get('electricity_consumption_id') and not vals.get('water_consumption_id'):
            is_utility = vals.get('invoice_type_id') and self.env['invoice.type'].browse(vals['invoice_type_id']).type == 'utility'
            utility_period_to = vals['utitlity_period_to']
            if is_utility:
                vals.update({'invoice_date': utility_period_to})

        return super().create(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    new_value = fields.Float('New Index')
    last_value = fields.Float('Last Index')
    multiplier = fields.Float('Multiplier', default=1.0)
    radio_cosfi = fields.Float('Radio Cosfi', digits=(16, 2))
    radio_kfactor = fields.Float('Radio K (%)', digits=(16, 2))
    utility_quantity = fields.Float()
    connection_quantity = fields.Float(
        string='Power Consumption/Increase Transformer Capacity', digits=(16, 4))
    connection_rate = fields.Float(string='Connection Rate', default=1.0)
    electricity_point_id = fields.Many2one(
        comodel_name='electricity.point',
        compute="_compute_data_journal_entry",
        store=True, readonly=False,
        string='Metering Point',
    )

    @api.depends('product_id', 'product_uom_id',
                 'move_id.invoice_type_id.type', 'move_id.invoice_type_id',
                 'date_from', 'date_to', 'leasing_price_unit', 'area',
                 'connection_quantity', 'connection_rate', 
                 'radio_kfactor', 'move_id.utility_electricity_type', 'move_id.utility_total_amount')
    def _compute_price_unit(self):
        result = super()._compute_price_unit()
        for line in self:
            if line.move_id.utility_electricity_type == 'reactive_power' and line.move_id.invoice_type_code == 'utility':
                line.price_unit = line.move_id.utility_total_amount * line.radio_kfactor / 100
            if line.move_id.utility_electricity_type == 'connection_charge' and line.move_id.invoice_type_code == 'utility':
                line.price_unit = line.connection_quantity * line.connection_rate / 100
        return result

    @api.depends('display_type', 'move_id.invoice_type_id', 'move_id.invoice_type_id.type',
                 'connection_quantity', 'connection_rate', 
                 'product_uom_id', 'radio_kfactor', 'move_id.utility_electricity_type')
    def _compute_quantity(self):
        result = super()._compute_quantity()
        for line in self:
            if line.move_id.utility_electricity_type == 'reactive_power' and line.move_id.invoice_type_code == 'utility':
                line.quantity = 1
            if line.move_id.utility_electricity_type == 'connection_charge' and line.move_id.invoice_type_code == 'utility':
                line.quantity = 1
        return result

    @api.depends("move_id.electricity_point_id")
    def _compute_data_journal_entry(self):
        super()._compute_data_journal_entry()
        for line in self:
            line.electricity_point_id = line.move_id.electricity_point_id

    @api.onchange('new_value', 'last_value', 'multiplier')
    def onchange_value_consumption(self):
        diff_value = self.new_value - self.last_value
        self.quantity = (diff_value if diff_value > 0 else 0) * self.multiplier

    @api.onchange('quantity')
    def _onchange_utility_quantity(self):
        self.utility_quantity = self.quantity  

    def _generate_report_payment_request(self):
        vals = super()._generate_report_payment_request()
        vals.update({
            'last_value': formatLang(self.env, self.last_value, digits=2) if self.last_value > 0 else '',
            'new_value': formatLang(self.env, self.new_value, digits=2) if self.new_value > 0 else '',
            'multiplier': self.multiplier if self.last_value > 0 else '',
            'radio_cosfi': self.radio_cosfi,
            'radio_kfactor': self.radio_kfactor,
            'utility_quantity': formatLang(self.env, self.utility_quantity, digits=2),
            'connection_quantity': formatLang(self.env, self.connection_quantity, digits=0),
            'connection_rate': f"{formatLang(self.env, self.connection_rate, digits=1)}%"
        })
        return vals
