from odoo import api, fields, models, _


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    bank_address = fields.Char(
        compute='_compute_bank_address', string="Bank's Address")
    partner_id = fields.Many2one(required=False)
    partner_cr_id = fields.Many2one('res.partner.cr')

    @api.depends('bank_id.street', 'bank_id.street2', 'bank_id.zip', 'bank_id.city', 'bank_id.state', 'bank_id.country')
    def _compute_bank_address(self):
        for rec in self:
            addr_format = [
                rec.bank_id.street,
                rec.bank_id.street2,
                rec.bank_id.zip,
                rec.bank_id.city,
                rec.bank_id.state.name,
                rec.bank_id.country.name
            ]
            rec.bank_address = ", ".join(
                text for text in addr_format if isinstance(text, str))

    @api.depends('partner_id', 'partner_cr_id')
    def _compute_account_holder_name(self):
        bank_cr_ids = self.filtered(lambda bank: not bank.partner_id)
        for bank in bank_cr_ids:
            bank.acc_holder_name = bank.acc_holder_name or bank.partner_cr_id.name
        self_super = self - bank_cr_ids
        super(ResPartnerBank, self_super)._compute_account_holder_name()
