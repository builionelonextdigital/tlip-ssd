# # -*- coding: utf-8 -*-


# from odoo import models, api


# class Company(models.Model):
#     _inherit = "res.company"

#     @api.model
#     def create(self, vals):
#         res = super(Company, self).create(vals)
#         if res:
#             business_activities_config = self.env["business.activities.config"].search([
#                 ("active", "=", True),
#                 ("company_id", "=", self.env.company.id),
#             ])
#             if business_activities_config:
#                 business_activities_config.with_context(create_company=True, new_company=res.id).create_missing_field_ids()
#         return res