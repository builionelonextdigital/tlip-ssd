# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    def update_profit_loss_statement(self):
        business_activities_config = self.env["business.activities.config"].search([
                ("active", "=", True),
                ("company_id", "=", self.env.company.id),
            ])
        if business_activities_config:
            raise ValidationError('Data was created!')
        business_activities_config.with_context(create_company=True, new_company=self.env.company.id).create_missing_field_ids()