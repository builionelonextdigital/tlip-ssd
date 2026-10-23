from odoo import models, fields


class CheckPartnerExistWizard(models.TransientModel):
    _name = 'check.partner.exist.wizard'
    _description = 'Check Partner Exist Wizard'

    vat = fields.Char('Tax Code/ID Code', required=True)
    check_type = fields.Selection(
        [('vendor', 'Vendor'), ('customer', 'Customer')], required=True)

    def button_check_exist(self):
        partner = self.env['res.partner'].search(
            [('vat', '=', self.vat), '|', ('vendor_state', '=', 'approved'), ('customer_state', '=', 'approved')], limit=1)
        return partner
