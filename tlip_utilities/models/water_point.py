import logging
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from datetime import timedelta
from odoo.tools.date_utils import end_of

from odoo import models, fields, api, _
from odoo.tools import groupby

_logger = logging.getLogger(__name__)


class WaterPoint(models.Model):
    _name = "water.point"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_names_search = ['name', 'qr_code']
    _description = "Water Point"

    name = fields.Char("Water Point", required=True, tracking=True)
    measurement_point_location_name = fields.Char(string="Measurement Point Location Name", tracking=True)
    qr_code = fields.Char(string="QR Code", required=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirm')], string="State",
        default='draft', tracking=True, required=True)
    partner_id = fields.Many2one('res.partner', 'Customer',
                                 tracking=True, required=True)
    land_plot_id = fields.Many2one(
        'stock.location', required=False, tracking=True)
    land_plot_name = fields.Char(string='Land Plot', compute='_compute_land_plot_name', store=True, readonly=False)
    auto_issue_payment = fields.Boolean('Automatically Issue Payment Request')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)
    signing_date = fields.Date('Signing Date', tracking=True)
    starting_date = fields.Date('Starting Date', tracking=True)
    ending_date = fields.Date('Ending Date', tracking=True)
    connection_signing_date = fields.Date(
        'Connection Signing Date', tracking=True)
    meter_code = fields.Char(
        'Meter Code', tracking=True)
    note = fields.Text(
        'Notes', tracking=True)
    payment_due_date = fields.Integer(string='Payment Due Date')
    contract_payment_article = fields.Char()
    contract_number = fields.Char(
        'Contract Number', tracking=True, required=True)
    customer_contact_ids = fields.Many2many('res.partner',
                                            compute='_compute_customer_contact_ids', 
                                            domain="[('parent_id', '=', partner_id)]", string='Customer Contacts')
    tax_apply_type = fields.Selection([('epe', 'EPE'), ('non_epe', 'Non-EPE')], string="Tax Apply", default="non_epe")
    invoice_address_id = fields.Many2one('res.partner', string='Invoice Address')
    consumption_record_schedule_ids = fields.One2many('consumption.record.schedule', 'water_point_id')
    sync_status = fields.Selection([('done', 'Done'),
                                    ('in_progress', 'In Progress')])
    pricelist_id = fields.Many2one('utilities.pricelist', string='Pricelist', domain="[('utility_type', '=', 'water')]")
    included_fee_ids = fields.Many2many('product.product', string='Included Fees')
    email_for_payment = fields.Char()
    email_for_invoice = fields.Char()
    connection_contract_number = fields.Char(
        'Connection Contract Number', tracking=True)
    connection_contract_payment_article = fields.Char()
    connection_signing_date = fields.Date(
        'Connection Signing Date', tracking=True)
    active = fields.Boolean(default=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('measurement_point_location_name', operator, name), ('qr_code', operator, name)]
        water_points = self.search_fetch(domain + args, ['name'], limit=limit)
        return [(point.id, point.name) for point in water_points.sudo()]

    @api.depends('land_plot_id')
    def _compute_land_plot_name(self):
        for record in self:
            record.land_plot_name = record.land_plot_id.name
            
    @api.depends('partner_id')
    def _compute_customer_contact_ids(self):
        for record in self:
            record.customer_contact_ids = [(6, 0, record.partner_id.child_ids.ids)]

    def _compute_sync_status(self):
        for record in self:
            record.sync_status = 'done' if all(l.water_consumption_id for l in record.consumption_record_schedule_ids) else 'in_progress'

    def action_confirm(self):
        self.state = 'confirm'

    def action_reset(self):
        self.state = 'draft'

    def _run(self, company, date_from, date_to):
        credential_data = company._get_credential_data('water')
        positions = [f"'{point.qr_code}'" for point in self]
        sql_query = f'''
            SELECT * FROM `unity_data`
            WHERE modify_date >= '{date_from}' and modify_date <= '{date_to}'
            and qr_code in ({",".join(positions)})
        '''
        datas = company._execute_mysql_query(
            credential_data, sql_query)
        grouped_data = defaultdict(list)
        for data in datas:
            key = (data.get('qr_code'), data.get('modify_date'))
            grouped_data[key].append(data)

        # Collect all created/updated consumptions
        consumptions = self.env['water.consumption']
        for key, values in grouped_data.items():
            point = self.filtered_domain([('qr_code', '=', key[0])])
            if not point:
                continue
            consumption = point._generate_water_consumption(values)
            if consumption:
                consumptions |= consumption

        # Flush all consumption and line changes to database before approval
        self.env.cr.flush()

        self.mapped('consumption_record_schedule_ids')._compute_water_consumption_id()
        self._compute_sync_status()

        # Auto-approve all consumptions after everything is flushed
        for consumption in consumptions.filtered(lambda c: c.state == 'draft'):
            try:
                consumption.action_submit_approval()
            except Exception as e:
                consumption.message_post(body=_("Auto approve failed: %s" % e))
                _logger.error("Failed to auto approve water consumption %s: %s", consumption.id, e)

    @api.model
    def _synchronize_consumption(self,  date_from=fields.Datetime.now(), date_to=fields.Datetime.now()):
        date_from = date_from.replace(hour=0, minute=0, second=0)
        date_to = date_to.replace(hour=23, minute=59, second=59)
        points = self.search([('state', '=', 'confirm')])
        for company, water_points in groupby(points, lambda p: p.company_id):
            if not company.water_server:
                continue
            water_points = self.concat(*water_points)

            def divide_chunks():
                for i in range(0, len(water_points), 30):
                    yield water_points[i:i + 30]

            for chunk in divide_chunks():
                chunk.with_delay()._run(company, date_from, date_to)

    def _generate_water_consumption(self, values):
        self.ensure_one()
        consumption_env = self.env['water.consumption']
        start_value = values[0]
        record_date = start_value.get('to_date')
        record_date = fields.Date.to_date(record_date) + timedelta(days=1)
        consumption = consumption_env.search(
            [('water_point_id', '=', self.id),
                ('record_date', '=', record_date)], limit=1)
        if consumption and consumption.state != 'draft':
            return consumption
        if not consumption:
            currency_code = start_value.get('currency', False)
            currency = self.env['res.currency'].search(
                [('name', '=', currency_code)])
            if not currency:
                return None
            
            date_maturity = (record_date + relativedelta(months=1)).replace(day=1)
            try:
                payment_due_date = self.payment_due_date or self.company_id.water_payment_due_date
                if payment_due_date == -1:
                    date_maturity = end_of(date_maturity, 'month')
                else:
                    date_maturity = date_maturity.replace(day=int(payment_due_date))
            except Exception as err:
                _logger.error(f'Payment Due Date error: {str(err)}')
            consumption = consumption_env.create({
                'partner_id': self.partner_id.id,
                'record_date': record_date,
                'water_point_id': self.id,
                'date_from': start_value.get('from_date'),
                'date_to': start_value.get('to_date'),
                'invoice_due_date': date_maturity,
                'company_id': self.company_id.id,
                'currency_id': currency.id,
                'source': 'water_app'
            })
        line_vals = []
        for value in values:
            default_code = value.get('item_code', False)
            product = self.company_id.get_product_by_code('water', default_code)
            if product:
                check_existed = consumption.line_ids.filtered(
                    lambda line: line.product_id == product)
                if not check_existed:
                    consumption_line = self._prepare_water_consumption_line(
                        product, value)
                    line_vals.append((0, 0, consumption_line))
                    pricelist = self.pricelist_id 
                    for included_fee in self.included_fee_ids:
                        pricelist_line = pricelist.pricelist_item_ids.filtered(lambda l: l.product_id == included_fee)
                        unit_price = 0
                        if pricelist_line:
                            unit_price = pricelist_line[0].unit_price
                        included_consumption_line = consumption_line.copy()
                        included_consumption_line.update({
                            'product_id': included_fee.id,
                            'unit_price': unit_price,
                            'amount': included_consumption_line['quantity'] * unit_price,
                        })
                        line_vals.append((0, 0, included_consumption_line))
        if line_vals:
            consumption.write({'line_ids': line_vals})

        return consumption

    def _prepare_water_consumption_line(self, product, value):
        return {
            'product_id': product.id,
            'start_value': value.get('start_value'),
            'end_value': value.get('end_value'),
            'quantity': float(value.get('increase_value', 0.0)),
            'unit_price': value.get('unit_price'),
            'vat': value.get('tax_amount'),
            'amount': value.get('total_price'),
            'exchange_rate': value.get('exchange_rate'),
        }

    @api.model
    def _search_display_name(self, operator, value):
        return super()._search_display_name(operator, value)
