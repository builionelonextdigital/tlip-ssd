from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class AccountPayment(models.Model):
    _inherit = "account.payment"

    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order')
    procurement_contract_id = fields.Many2one(
        related='purchase_order_id.requisition_id')
    task_id = fields.Many2one(
        'procurement.task', related='purchase_order_id.task_id')
    request_purchase_id = fields.Many2one(
        'request.purchase', string='Request for Goods/Service', copy=False)
    request_line_ids = fields.Many2many(
        'request.purchase.line', compute='_compute_request_line_ids', store=True)
    amount_tax = fields.Monetary(string='Actual Tax Amount')
    budget_department_responsible_job_id = fields.Many2one('hr.job', check_company=True,
                                                           compute="_compute_budget_department_responsible",
                                                           compute_sudo=True,
                                                           store=True)

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order(self):
        self.development_project_id = self.purchase_order_id.development_project_id
        self.development_phase_id = self.purchase_order_id.development_phase_id

    @api.depends('task_id', 'request_purchase_id')
    def _compute_request_line_ids(self):
        for record in self:
            request_lines = record.task_id.request_line_ids | record.request_purchase_id.request_line_ids
            record.request_line_ids = [(6, 0, request_lines.ids)]

    @api.depends('task_id', 'request_purchase_id', 'purchase_order_id', 'analytic_distribution')
    def _compute_budget_department_responsible(self):
        for record in self:
            task = record.task_id
            budget_department = record.request_purchase_id.budget_department_id.with_context(
                company_id=record.company_id.id)
            requisition = record.purchase_order_id.requisition_id

            budget_department_responsible_job = (
                task.budget_department_responsible_job_id or
                budget_department.job_id or
                requisition.budget_department_responsible_job_id
            )

            if not budget_department_responsible_job:
                budget_department_responsible_job = (
                    record.get_department_job_on_analytic_distribution(
                        record_name=record.name or record.request_payment_number,
                        company_id=record.company_id.id
                    )
                )

            record.budget_department_responsible_job_id = budget_department_responsible_job

    def action_submit_approval(self):
        res = super().action_submit_approval()
        for record in self:
            if record.is_request_payment and record.payment_type == "outbound" and not record.is_advance_payment and not record.auto_reconcile_item_ids:
                raise UserError(
                    _("Bill Payment %s cannot be submitted as it does not have any reconciliation items.") % record.name)

            if record.auto_reconcile_item_ids and float_compare(record.amount, sum(record.auto_reconcile_item_ids.mapped('move_id.amount_residual')), 2) > 0:
                reconcile_item_names = list(filter(bool, record.auto_reconcile_item_ids.mapped('move_id.name')))
                raise ValidationError(_(
                    "Bill Payment %s cannot be submitted for approval as it exceeds the residual amount of the reconciliation item %s."
                )
                    % (record.name or record.request_payment_number, ", ".join(reconcile_item_names))
                )
        return res
