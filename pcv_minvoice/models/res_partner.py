from odoo import models


class Partner(models.Model):
    _inherit = 'res.partner'

    def get_full_partner_address(self):
        self.ensure_one()
        address_arr = [self.street,
                       self.zip,
                       self.city,
                       self.state_id.name,
                       self.country_id.name]
        return ' '.join([addr for addr in address_arr if addr and isinstance(addr, str)])
