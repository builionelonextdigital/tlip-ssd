# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountGroup(models.Model):
    _inherit = "account.group"

    code = fields.Char(string="Code", copy=False)

