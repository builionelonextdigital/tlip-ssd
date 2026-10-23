from odoo import models, fields, api, _


class ElectricityCategory(models.Model):
    _name = "electricity.category"
    _description = "Electricity Category"

    name = fields.Char(required=True)
