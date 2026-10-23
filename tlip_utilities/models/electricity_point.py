import logging
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import end_of, start_of
from odoo.tools import groupby, float_round


_logger = logging.getLogger(__name__)

class ElectricityPoint(models.Model):
    _name = "electricity.point"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Electricity Point"

    name = fields.Char("Electricity Point", required=True, tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirm')], string="State",
        default='draft', tracking=True, required=True)
    electricity_point_name = fields.Char(
        compute="_compute_electricity_point_name",
        store=True, required=True, tracking=True, readonly=False
    )
    electricity_type = fields.Selection(
        [('normal', 'Normal'), ('solar', 'Solar')],
        string='Electricity Type', default='normal', tracking=True, required=True)
    electricity_categ_id = fields.Many2one('electricity.category',
                                           'Electricity Category',
                                           tracking=True, required=True)
    auto_issue_payment = fields.Boolean('Automatically Issue Payment Request')
    partner_id = fields.Many2one('res.partner', 'Customer',
                                 tracking=True, required=True)
    partner_code = fields.Char(
        'Customer Code', related='partner_id.customer_code')
    land_plot_id = fields.Many2one(
        'stock.location', required=False, tracking=True)
    land_plot_name = fields.Char(string='Land Plot', compute='_compute_land_plot_name', store=True, readonly=False)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)
    contract_number = fields.Char(
        'Contract Number', tracking=True, required=True)
    signing_date = fields.Date('Signing Date', tracking=True)
    starting_date = fields.Date('Starting Date', tracking=True)
    ending_date = fields.Date('Ending Date', tracking=True)
    meter_code = fields.Char(
        'Meter Code', tracking=True)
    note = fields.Text(
        'Notes', tracking=True)
    contract_payment_article = fields.Char()
    connection_contract_number = fields.Char(
        'Connection Contract Number', tracking=True)
    connection_contract_payment_article = fields.Char()
    connection_signing_date = fields.Date(
        'Connection Signing Date', tracking=True)

    payment_due_date = fields.Integer(string='Payment Due Date')
    customer_contact_ids = fields.Many2many('res.partner',
                                            compute='_compute_customer_contact_ids',
                                            domain="[('parent_id', '=', partner_id)]", string='Customer Contacts')
    invoice_address_id = fields.Many2one(
        'res.partner', string='Invoice Address')
    count_record_in_month = fields.Integer(
        compute='_compute_count_record_in_month')
    record_status = fields.Selection([('no', 'To Sync'),
                                      ('partial', 'Paritall Sync'),
                                      ('fully', 'Fully Sync')])
    tax_apply_type = fields.Selection(
        [('epe', 'EPE'), ('non_epe', 'Non-EPE')], string="Tax Apply", default="non_epe")
    consumption_record_schedule_ids = fields.One2many('consumption.record.schedule', 'electricity_point_id')
    sync_status = fields.Selection([('done', 'Done'),
                                    ('in_progress', 'In Progress')])    
    pricelist_id = fields.Many2one('utilities.pricelist', string='Pricelist', domain="[('utility_type', '=', 'electricity')]")
    email_for_payment = fields.Char()
    email_for_invoice = fields.Char()
    active = fields.Boolean(default=True)

    @api.depends('land_plot_id')
    def _compute_land_plot_name(self):
        for record in self:
            record.land_plot_name = record.land_plot_id.name

    def _compute_count_record_in_month(self):
        today = fields.Date.today()
        for record in self:
            record.count_record_in_month = len(record.consumption_record_schedule_ids.mapped('electricity_consumption_id'))

    @api.depends('partner_id')
    def _compute_customer_contact_ids(self):
        for record in self:
            record.customer_contact_ids = [
                (6, 0, record.partner_id.child_ids.ids)]

    def _compute_sync_status(self):
        for record in self:
            record.sync_status = 'done' if all(l.electricity_consumption_id for l in record.consumption_record_schedule_ids) else 'in_progress'

    @api.depends('name')
    def _compute_electricity_point_name(self):
        for record in self:
            record.electricity_point_name = record.electricity_point_name or record.name

    def action_confirm(self):
        self.state = 'confirm'

    def action_reset(self):
        self.state = 'draft'

    def _run(self, company, date_from, date_to):
        credential_data = company._get_credential_data('power')
        positions = [f"'{point.name}'" for point in self]
        database = credential_data.get('database')
        if company.power_database != 'MAMR':
            sql_query = f'''
                SELECT [Ma_diemdo]
                    ,[ThoiGianCapNhat]
                    ,[ThoiGianBatDau]
                    ,[ThoiGianKetThuc]
                    ,[Bieu]
                    ,[ChiSoDau]
                    ,[ChiSoCuoi]
                    ,[PhiDauNoi]
                    ,[HeSoDauNoi]
                    ,[hsn]
                    ,[DienNang]
                    ,[DonGia]
                    ,[ThanhTien]
                    ,[VAT]
                FROM [{database}].[dbo].[HOADON]
                WHERE ThoiGianKetThuc BETWEEN '{date_from}' and '{date_to}' and Ma_diemdo in ({",".join(positions)})
            '''
        else:
            sql_query = f'''
                SELECT [ThoiGianCapNhat]
                    ,[MaCongTo]
                    ,[ThoiGianBatDau]
                    ,[ThoiGianKetThuc]
                    ,[Bieu]
                    ,[ChiSoDau]
                    ,[ChiSoCuoi]
                    ,[DienNang]
                    ,[DonGia]
                    ,[ThanhTien]
                    ,[PhiDauNoi]
                    ,[HeSoDauNoi]
                    ,[VAT]
                FROM [{database}].[dbo].[HOADON]
                WHERE ThoiGianKetThuc BETWEEN '{date_from}' and '{date_to}' and MaCongTo in ({",".join(positions)})
            '''
        datas, msg = company._execute_mssql_query(
            credential_data, sql_query)
        if msg != 'Success':
            raise ValidationError(msg)
        grouped_data = defaultdict(list)
        for data in datas:
            if 'Ma_diemdo' in data:
                key = (data.get('Ma_diemdo'), data.get('ThoiGianKetThuc'))
            else:
                key = (data.get('MaCongTo'), data.get('ThoiGianKetThuc'))
            grouped_data[key].append(data)

        # Collect all created/updated consumptions
        consumptions = self.env['electricity.consumption']
        for key, values in grouped_data.items():
            point = self.filtered_domain([('name', '=', key[0])])
            if not point:
                continue
            consumption = point._generate_electricity_consumption(values)
            if consumption:
                consumptions |= consumption

        # Flush all consumption and line changes to database before approval
        self.env.cr.flush()

        self.mapped('consumption_record_schedule_ids')._compute_electricity_consumption_id()
        self._compute_sync_status()

        # Auto-approve all consumptions after everything is flushed
        for consumption in consumptions.filtered(lambda c: c.state == 'draft'):
            try:
                consumption.action_submit_approval()
            except Exception as e:
                consumption.message_post(body=_("Auto approve failed: %s" % e))
                _logger.error("Failed to auto approve electricity consumption %s: %s", consumption.id, e)

    @api.model
    def _synchronize_consumption(self, date_from=fields.Datetime.now(), date_to=fields.Datetime.now()):
        date_from = date_from.replace(hour=0, minute=0, second=0)
        date_to = date_to.replace(hour=23, minute=59, second=59)
        points = self.search([('state', '=', 'confirm')])
        for company, electricity_points in groupby(points, lambda p: (p.company_id)):
            if not company.power_server:
                continue
            electricity_points = self.concat(*electricity_points)

            def divide_chunks():
                for i in range(0, len(electricity_points), 30):
                    yield electricity_points[i:i + 30]

            for chunk in divide_chunks():
                chunk.with_delay()._run(company, date_from, date_to)

    def _generate_electricity_consumption(self, values):
        self.ensure_one()
        consumption_env = self.env['electricity.consumption']
        start_value = values[0]
        record_date = start_value.get('ThoiGianKetThuc', False)
        record_date = fields.Date.to_date(record_date)
        consumption = consumption_env.search(
            [('electricity_point_id', '=', self.id),
                ('record_date', '=', record_date)], limit=1)
        if consumption and consumption.state != 'draft':
            return consumption
        if not consumption:
            due_date = record_date + timedelta(days=int(self.payment_due_date or self.company_id.electricity_payment_due_date))
            consumption = consumption_env.create({
                'partner_id': self.partner_id.id,
                'record_date': record_date,
                'electricity_point_id': self.id,
                'date_from': start_value.get('ThoiGianBatDau'),
                'date_to': start_value.get('ThoiGianKetThuc'),
                'company_id': self.company_id.id,
                'source': 'power_app',
                'invoice_due_date': due_date,
                'currency_id': self.company_id.currency_id.id
            })
        update_vals, line_vals = {}, []
        electricity_connection_charge = 0.0
        connection_rate = 0.0
        for value in values:
            Bieu = value.get('Bieu', False)
            connection_rate = float(value.get('HeSoDauNoi', 0.0) or 0.0) * 100
            if Bieu == 'VCG' and float(value.get('ThanhTien', 0)) == 0:
                continue
            quantity = float(value.get('DienNang', 0.0))
            if Bieu == 'COSPHI':
                kfactor = self.env['electricity.kfactor']._get_kfactor(
                    quantity)
                update_vals.update({'cosphi': quantity, 'kfactor': kfactor})
            else:
                electricity_connection_charge += float(value.get('ThanhTien', 0.0))
                product = self.company_id.get_product_by_code('electricity', Bieu)
                if product:
                    check_existed = consumption.line_ids.filtered(
                        lambda line: line.product_id == product)
                    if not check_existed:
                        consumption_line = self._prepare_electricity_consumption_line(
                            product, value)
                        if Bieu == 'VCG' and value.get('ThanhTien', 0) > 0:
                            consumption_line['is_reactive_power_line'] = True
                            update_vals.update(
                                {'reative_power_quantity': quantity})
                        line_vals.append((0, 0, consumption_line))
        if line_vals:
            update_vals.update({
                'line_ids': line_vals,
                'electricity_connection_charge': float_round(electricity_connection_charge * connection_rate / 100, 0),
                'connection_rate': connection_rate
            })
        if update_vals:
            consumption.write(update_vals)

        return consumption

    def _prepare_electricity_consumption_line(self, product, value):
        return {
            'product_id': product.id,
            'start_meter_reading': value.get('ChiSoDau'),
            'end_meter_reading': value.get('ChiSoCuoi'),
            'multiplier': value.get('hsn'),
            'quantity': float(value.get('DienNang', 0.0)),
            'unit_price': value.get('DonGia'),
            'amount': value.get('ThanhTien'),
        }
