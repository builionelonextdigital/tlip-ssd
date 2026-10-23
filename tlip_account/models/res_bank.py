from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import SQL


class ResBank(models.Model):
    _inherit = "res.bank"

    def open_bank_exchange_rate(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_account.bank_exchange_rate_action')
        action.update({
            'target': 'current',
            'domain': [('bank_id', '=', self.id)],
            'context': {
                'default_bank_id': self.id
            }
        })
        return action
    