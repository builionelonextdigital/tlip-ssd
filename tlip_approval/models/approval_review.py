from odoo import fields, models, _


class ApprovalReview(models.Model):
    _name = 'approval.review'
    _description = 'Approval Review'

    approver_ids = fields.Many2many('res.users', string="Approver(s)")
    approval_request_id = fields.Many2one('approval.request')
    old_value = fields.Char('Original Clause')
    new_value = fields.Char('Revised Clause')
    reason = fields.Char('Reason to revise/supplement')