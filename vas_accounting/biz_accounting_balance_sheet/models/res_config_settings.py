# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    business_cycle = fields.Integer("Business cycle (Month)")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    business_cycle = fields.Integer("Business cycle (Month)", related="company_id.business_cycle", readonly=False)


    def update_accounting_balance_sheet(self):
        accounting_balance_sheet = self.env["accounting.balance.sheet"].search([
                ("active", "=", True),
                ("company_id", "=", self.env.company.id),
                ("report_type", "=", "statements_cash_flows")
            ])
        if accounting_balance_sheet:
            raise ValidationError('Data was created!')
        accounting_balance_sheet.with_context(create_company=True, new_company=self.env.company.id).create_missing_field_ids()