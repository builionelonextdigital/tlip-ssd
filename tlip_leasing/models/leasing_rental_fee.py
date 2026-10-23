from dateutil.relativedelta import relativedelta

from odoo import models, fields, api

class RentalFee(models.Model):
    _name = 'leasing.rental.fee'
    _description = 'Rental Fee'

    agreement_id = fields.Many2one('leasing.agreement')
    supplement_id = fields.Many2one('leasing.supplement')
    termination_id = fields.Many2one('leasing.termination')
    fee_type_id = fields.Many2one('product.product', domain=[('type', '=', 'service')], required=True)
    uom_id = fields.Many2one('uom.uom', related='fee_type_id.uom_id', readonly=True)
    area = fields.Float(string='Area',compute="_compute_area")
    currency_id = fields.Many2one('res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id)
    price_unit = fields.Monetary('Price Unit')
    amount = fields.Monetary(compute='_compute_amount')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    line_number = fields.Integer('No.', compute='_compute_line_number')
    location_start = fields.Char('Start')
    location_end = fields.Char('End')
    number_of_pipes = fields.Integer('No. of pipe')
    telecom_line_length = fields.Float('Length of telecommunication line')
    premium_excluded_vat = fields.Float('Premium Excluded VAT')

    @api.depends('agreement_id.rental_fee_ids', 'supplement_id.rental_fee_ids', 'termination_id.rental_fee_ids')
    def _compute_line_number(self):
        for record in self:
            leasing_rec = record.agreement_id or record.supplement_id or record.termination_id
            rental_fees = leasing_rec.rental_fee_ids
            record.line_number = rental_fees._origin.ids.index(record._origin.id) + 1 if record._origin.id else 1

    @api.depends('agreement_id.area', 'supplement_id.area', 'termination_id.area')
    def _compute_area(self):
        for record in self:
            agreement = record.agreement_id or record.supplement_id or record.termination_id
            record.area = agreement.area
    
    @api.depends('date_from', 'date_to', 'price_unit', 'area')
    def _compute_amount(self):
        for record in self:
            if record.date_from and record.date_to:
                delta = relativedelta(record.date_to, record.date_from)
                months = delta.years * 12 + delta.months + (1 if delta.days > 0 else 0)
                years = delta.years + (1 if delta.months > 0 or delta.days > 0 else 0)
                if record.uom_id.id == self.env.ref('tlip_leasing.product_uom_vnd_m2_month').id:
                    record.amount = months * record.price_unit * record.area
                elif record.uom_id.id == self.env.ref('tlip_leasing.product_uom_vnd_year_m2').id:
                    record.amount = years * record.price_unit * record.area
                else:
                    record.amount = record.price_unit
            else:
                record.amount = record.price_unit