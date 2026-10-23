# -*- coding: utf-8 -*-
from odoo import models, api


class Company(models.Model):
    _inherit = "res.company"

    @api.model
    def create(self, vals):
        res = super(Company, self).create(vals)
        if res:
            cash_flows = self.env["cash.flows"].search([
                ("active", "=", True),
                ("company_id", "=", self.env.company.id),
                ("report_type", "=", "statements_cash_flows")
            ])
            if cash_flows:
                cash_flows.with_context(create_company=True, new_company=res.id).create_missing_cash_flow_field_ids()
        return res