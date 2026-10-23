from odoo import models, fields, api


class UomUom(models.Model):
    _inherit = 'uom.uom'

    leasing_type = fields.Selection([
        ('vnd', 'VND'),
        ('vnd_m', 'VND/month'),
        ('vnd_m2', 'VND/m2'),
        ('vnd_m2m', 'VND/m2/month'),
        ('vnd_m2y', 'VND/m2/year')], string='Uom Leasing Type')
    uom_invoice_vn = fields.Char('UoM VN')
    uom_invoice_en = fields.Char('UoM EN',)