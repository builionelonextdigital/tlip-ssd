# -*- coding: utf-8 -*-

from odoo import models


class IrActionsAccountPublicDiary(models.AbstractModel):
    _name = 'ir_actions_account_public_diary'
    _description = 'Technical model for account public diary'

    def _get_readable_fields(self):
        return self.env['ir.actions.actions']._get_readable_fields()