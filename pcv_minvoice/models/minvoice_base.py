from odoo import models, fields, api, _

from ..const import PAYMENT_METHOD_SELECTION


ORIGINAL_MINVOICE_FIELD = [
    'minvoice_template_code',
    'minvoice_template_id',
    'minvoice_no',
    'minvoice_issued_date'
]


class MInvoiceBase(models.AbstractModel):
    _name = "minvoice.base"
    _description = "MInvoice Base Model, used in Account Move and MInvoice Action Wizard"

    minvoice_template_payment_method = fields.Selection(
        selection=PAYMENT_METHOD_SELECTION,
        string="Hình thức thanh toán", tracking=True,
        compute="_compute_minvoice", store=True, readonly=False, default='transfer')
    minvoice_template_code = fields.Char(
        string="Mẫu hóa đơn", tracking=True,
        compute="_compute_minvoice", store=True, readonly=False)
    minvoice_template_id = fields.Many2one(
        'minvoice.template', string="Ký hiệu hóa đơn", tracking=True)
    minvoice_issued_date = fields.Datetime(
        string='Ngày lập hóa đơn', tracking=True, copy=False)

    original_invoice_id = fields.Many2one(
        'account.move', string="Hóa đơn gốc")
    original_minvoice_template_code = fields.Char(
        string="Mẫu hóa đơn gốc", tracking=True,
        compute="_compute_original_minvoice", store=True, readonly=False)
    original_minvoice_template_id = fields.Many2one(
        'minvoice.template', string="Ký hiệu hóa đơn gốc", tracking=True,
        compute="_compute_original_minvoice", store=True, readonly=False)
    original_minvoice_no = fields.Char(
        string="Số hóa đơn gốc", tracking=True,
        compute="_compute_original_minvoice", store=True, readonly=False)
    original_minvoice_issued_date = fields.Datetime(
        string='Ngày lập hóa đơn gốc', tracking=True,
        compute="_compute_original_minvoice", store=True, readonly=False)
    minvoice_note = fields.Char(string="Ghi chú")

    @api.model
    def get_minvoice_template_code_selection(self, domain=None):
        minvoice_template_rec = self.env['minvoice.template']
        code_selection = [(code, code)
                          for code in set(minvoice_template_rec.search(domain or []).mapped('code'))]

        return code_selection

    @api.depends('minvoice_template_id', 'minvoice_template_id.code', 'minvoice_template_id.payment_method')
    def _compute_minvoice(self):
        for rec in self:
            vals = rec._get_minvoice_template_vals(
                template_id=rec.minvoice_template_id)
            rec.update(vals)

    @api.depends('original_invoice_id', 'original_minvoice_template_id')
    def _compute_original_minvoice(self):
        for rec in self:
            vals = {}
            if rec.original_invoice_id:
                original_invoice_id = rec.original_invoice_id
                vals = {f'original_{field}': getattr(original_invoice_id, field)
                        for field in ORIGINAL_MINVOICE_FIELD}
            else:
                vals = {f'original_{field}': getattr(rec, f'original_{field}')
                        for field in ORIGINAL_MINVOICE_FIELD}

            rec.update(vals)
            minvoice_template_id = rec.original_minvoice_template_id
            rec.original_minvoice_template_code = minvoice_template_id.code \
                if minvoice_template_id else rec.original_minvoice_template_code

    @api.onchange('minvoice_template_code')
    def _onchange_minvoice_template_code(self):
        if self.minvoice_template_id.code != self.minvoice_template_code:
            self.minvoice_template_id = False

    @api.onchange('original_minvoice_template_code')
    def _onchange_original_minvoice_template_code(self):
        if self.original_minvoice_template_id.code != self.original_minvoice_template_code:
            self.original_minvoice_template_id = False

    def _get_minvoice_template_vals(self, template_id, default_text=''):
        '''
            Helper code to get dictionary value calcuate from minvoice template
            Used in wizard pop up as well, with default text, eg. 'default_{field_name}'
        '''
        if template_id:
            return {f'{default_text}minvoice_template_{field}': getattr(template_id, field)
                    for field in ['code', 'payment_method']}
        else:
            return {f'{default_text}minvoice_template_{field}': getattr(self, f'minvoice_template_{field}')
                    for field in ['code', 'payment_method']}

    def get_selection_label(self, field_name, selection):
        selection_dict = dict(self._fields[field_name].selection)
        return selection_dict.get(selection, '')
    
    api.model
    def _valid_field_parameter(self, field, name):
        if name == 'tracking':
            return True
        return super(MInvoiceBase, self)._valid_field_parameter(field, name)
