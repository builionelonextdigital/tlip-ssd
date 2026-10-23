from odoo import models, fields, api, _


class ElectricityKfactor(models.Model):
    _name = "electricity.kfactor"
    _description = "Electricity K-factor"
    _rec_name = "kfactor"
    _order = 'cosphi desc'

    kfactor = fields.Float(required=True, string="K-factor")
    cosphi = fields.Float(required=True)
    
    @api.model
    def _get_kfactor(self, cosphi):
        record = self.search([('cosphi', '=', cosphi)], limit=1)
        if not record:
            record = self.search(['|', ('cosphi', '>', cosphi), ('cosphi', '<', cosphi)], limit=1)
        return record.kfactor
