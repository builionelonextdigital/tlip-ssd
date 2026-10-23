from odoo import models, fields

class HrJob(models.Model):
    _inherit = 'hr.job'

    name_vn = fields.Char(string="Vietnamese Name", required=True)
