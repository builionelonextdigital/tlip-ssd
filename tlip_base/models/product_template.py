from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    company_id = fields.Many2one(default=lambda self: self.env.company)
    
    @api.depends('name', 'default_code')
    def _compute_display_name(self):
        for template in self:
            template.display_name = template.name
