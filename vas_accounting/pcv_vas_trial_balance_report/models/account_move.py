# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, Command
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"
    
    def action_post(self):
        for move in self:
            if any(line.account_id.follow_by_partner and not line.partner_id for line in move.line_ids)\
                or any(line.account_id.follow_by_partner and not line.partner_id for line in move.line_ids):
                raise UserError(_('Please specify a partner for line have an account is followed by partner.'))
        return super().action_post()