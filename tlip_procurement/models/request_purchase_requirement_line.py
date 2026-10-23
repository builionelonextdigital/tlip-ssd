from odoo import _, fields, models


class RequestPurchaseRequirementLine(models.Model):
    _name = "request.purchase.requirement.line"
    _description = "Procurement Request Requirement Line"

    name = fields.Char('Criteria')
    description = fields.Text('Description')
    vendor_comment = fields.Text('Vendor Comment')
    request_id = fields.Many2one('request.purchase')
    procurement_task_id = fields.Many2one('procurement.task')
    purchase_id = fields.Many2one('purchase.order', ondelete='cascade')