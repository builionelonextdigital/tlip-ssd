# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import convert
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def update_cash_flows(self):
        cash_flows = self.env["cash.flows"].search([
                ("active", "=", True),
                ("company_id", "=", self.env.company.id),
                ("report_type", "=", "statements_cash_flows")
            ])
        if cash_flows:
            raise ValidationError('Data was created!')
        cash_flows.with_context(create_company=True, new_company=self.env.company.id).create_missing_cash_flow_field_ids()
