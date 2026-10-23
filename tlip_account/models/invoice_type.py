from odoo import api, fields, models, _


class InvoiceType(models.Model):
    _name = 'invoice.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Invoice Type'
    _rec_name = 'name_en'

    name_en = fields.Char('Name in EN', tracking=True, required=True)
    name_vn = fields.Char('Name in VN', tracking=True, required=True)
    report_payment_request_id = fields.Many2one('ir.actions.report', string='Report Payment Request')
    type = fields.Selection(
        selection=[
            ("leasing", "Leasing"),
            ("service", "Service"),
            ("utility", "Utility"),
            ("others", "Others")
        ], string="Type", default="others", tracking=True, required=True
    )
    utility_type = fields.Selection(
        [('electricity', 'Electricity'), ('water', 'Water')], string="Utility Type")
    utility_quantity_based_on = fields.Selection([('consumption', 'Consumption'),
                                                  ('quantity', 'Quantity')], default='consumption')
    leasing_type = fields.Selection(
        [('rental_fee', 'Rental'), ('management_fee', 'Management Fee')], string="Leasing Type")
    minvoice_template_ids = fields.Many2many('minvoice.template', string='E-Invoice Templates')
    payment_method = fields.Selection(selection=[
        ('TM/CK', 'TM/CK'),
        ('cash', 'Tiền mặt / Cash'),
        ('transfer', 'Chuyển khoản / Bank transfer')
    ], string="Hình thức thanh toán")
    product_category_ids = fields.Many2many('product.category', string='Product Categories')
    request_sequence_ids = fields.Many2many('ir.sequence', string='Request Payment Sequence')
    request_sequence_id = fields.Many2one('ir.sequence', compute='_compute_request_sequence_id')
    default_email_template_id = fields.Many2one('mail.template', string='Default Email Template')

    active = fields.Boolean(default=True)
    tax_calculation_rounding_method = fields.Selection([
        ('round_per_line', 'Round per Line'),
        ('round_globally', 'Round Globally'),
        ],
        required=True, default='round_per_line', string='Tax Calculation Rounding Method',
        help="This will enforce the tax calculation to be rounded per line or globally, it wont apply the tax calculation rounding method of the company for the invoice with this type"
    )

    @api.depends_context('company')
    def _compute_request_sequence_id(self):
        for record in self:
            record.request_sequence_id = record.request_sequence_ids.filtered(lambda r: self.env.company == r.company_id)[:1]
    
    def get_minvoice_template(self, company):
        return self.with_company(company).minvoice_template_ids.filtered(lambda r: r.company_id == company)[:1]
