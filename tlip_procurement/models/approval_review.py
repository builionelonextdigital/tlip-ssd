from odoo import fields, models, _


class ApprovalReview(models.Model):
    _inherit = 'approval.review'

    requisition_id = fields.Many2one('purchase.requisition')
