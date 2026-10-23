from odoo import fields, models


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('plan', "Plan Layout")], ondelete={'plan': 'cascade'})

    def _get_view_info(self):
        return {'plan': {'icon': 'fa fa-map'}} | super()._get_view_info()