from odoo import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    request_purchase_id = fields.Many2one(
        "request.purchase",
        string="Request for Goods/Service",
        compute="_compute_procurement_data",
        store=True,
    )
    task_id = fields.Many2one(
        "procurement.task",
        string="Procurement Task",
        compute="_compute_procurement_data",
        store=True,
    )

    @api.depends("move_line_id.request_purchase_line_id.request_id", "move_line_id.purchase_order_id.task_id")
    def _compute_procurement_data(self):
        for analytic_line in self:
            move_line = analytic_line.move_line_id
            line_ids = move_line.move_id.invoice_line_ids

            if move_line not in line_ids:
                analytic_line.task_id = False
                analytic_line.request_purchase_id = False
                continue

            # To handle the case where the move line does not have task_id or request_id directly
            parent_task_ids = line_ids.purchase_order_id.task_id
            parent_request_ids = line_ids.request_purchase_line_id.request_id
            analytic_line.task_id = move_line.purchase_order_id.task_id or parent_task_ids[:1]
            analytic_line.request_purchase_id = move_line.request_purchase_line_id.request_id or parent_request_ids[:1]
