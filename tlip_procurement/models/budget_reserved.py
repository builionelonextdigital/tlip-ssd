"""Budget Reservation Model for Procurement Module.

This module extends the base budget.reserved model to handle budget reservations
specifically for procurement requests. It tracks:
- Reserved budget amounts from submitted purchase requests
- Amounts committed through confirmed vendor selections
- Remaining available budget (reserved - used)
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from itertools import groupby
from collections import defaultdict

# State constants for request purchases and vendor selections
INACTIVE_REQUEST_STATES = ["draft", "rejected", "cancel"]
CONFIRMED_SELECTION_STATES = ["waiting_approval", "confirmed"]


class BudgetReserved(models.Model):
    _inherit = "budget.reserved"

    request_purchase_id = fields.Many2one(
        "request.purchase",
        string="Request for Goods/Service",
        required=True,
        copy=False,
        ondelete="cascade",
    )
    task_ids = fields.Many2many(
        "procurement.task", string="Tasks", compute="_compute_task_ids", store=True
    )
    amount = fields.Float(compute="_compute_budget_reserved_amount", store=True)

    @api.constrains("account_id", "request_purchase_id")
    def _check_unique_account_request_purchase(self):
        for record in self:
            if record.request_purchase_id:
                check_existed = self.search_count(
                    [
                        ("account_id", "=", record.account_id.id),
                        ("request_purchase_id", "=", record.request_purchase_id.id),
                        ("id", "!=", record.id),
                    ]
                )
                if check_existed > 0:
                    raise ValidationError(
                        "The combination of Budget Account and Request Purchase must be unique!"
                    )

    @api.depends("request_purchase_id.request_line_ids.task_id", "account_id")
    def _compute_task_ids(self):
        """Compute active tasks linked to this budget reservation.

        Only includes tasks that are not locked.
        """
        for br in self:
            request_lines = br.request_purchase_id.request_line_ids.filtered(
                lambda line, account=br.account_id: line.analytic_account_id == account
            )
            tasks = request_lines.mapped("task_id")
            br.task_ids = tasks.filtered(lambda t: not t.is_locked)

    @api.depends(
        "request_purchase_id.state",
        "request_purchase_id.analytic_line_ids",
        "task_ids.rfq_selection_ids.state",
        "task_ids.analytic_line_ids",
        "task_ids.current_contract_id.state",
    )
    def _compute_budget_reserved_amount(self):
        """Compute the remaining budget amount (reserved - used)."""
        # Linked Relationship Mapping: request_purchase_id -> task_id -> contract -> supplement
        #                                                             -> Posted Analytic
        # Since supplement is also considered, we need to call _compute_budget_reserved_amount in purchase.supplement model
        budget_reserved_mapping = self._get_reserved_mapping()
        for rec in self:
            reserved_amount = budget_reserved_mapping.get((rec.request_purchase_id.id, rec.account_id.id), 0.0)
            used_amount = rec._get_used_amount()
            rec.amount = reserved_amount - used_amount

    @api.model
    def action_unreserved_amount(self, tasks=None, requests=None):
        """Release budget reservations for completed or cancelled tasks."""
        budget_reserved_ids = self.env["budget.reserved"]
        if requests:
            budget_reserved_ids |= self.search([("request_purchase_id", "in", requests.ids)])
        if tasks:
            reserved_ids = self.search([("task_ids", "in", tasks.ids)])
            reserved_ids._compute_task_ids()
            budget_reserved_ids |= reserved_ids.filtered(lambda br: not br.task_ids)

        if budget_reserved_ids:
            budget_reserved_ids.sudo().unlink()

    def _get_reserved_mapping(self):
        """Calculate the total reserved amount for this budget reservation."""
        budget_reserved_mapping = defaultdict(float)
        RequestPurchaseLine = self.env["request.purchase.line"]
        for key, group in groupby(
            self.request_purchase_id.request_line_ids,
            lambda l: (l.request_id, l.task_id, l.task_id.current_contract_id),
        ):
            request, task, current_contract = key
            if current_contract.state == 'locked':
                continue

            # Prioritize supplements if the contract has active supplements and submitted
            active_supplements = current_contract.supplement_ids.filtered(lambda s: s.state in ('wait', 'approve', 'done'))
            if active_supplements and self._calculate_purchase_agreement_reserved(request, active_supplements[0], budget_reserved_mapping):
                continue

            # Prioritize contract lines if a contract is confirmed
            if self._calculate_purchase_agreement_reserved(request, current_contract, budget_reserved_mapping):
                continue

            # Next, check for confirmed vendor selections for the task
            if self._calculate_task_reserved(request, task, budget_reserved_mapping):
                continue

            # No confirmed vendor selection or contract; sum request lines
            request_lines = RequestPurchaseLine.concat(*group)
            for line in request_lines:
                key = (request.id, line.analytic_account_id.id)
                budget_reserved_mapping[key] += line.price_total

        return budget_reserved_mapping

    @api.model
    def _calculate_purchase_agreement_reserved(self, request_purchase, contract, reserved_mapping):
        """Calculate reserved amounts based on contract lines."""
        """Args:
            contract (record): The purchase.requisition or purchase.supplement record.
        """
        if not contract or (contract._name == "purchase.requisition" and contract.state != 'done'):
            return False

        for requisition_line in contract.line_ids.filtered(lambda l: l.analytic_distribution):
            for account, rate in requisition_line.analytic_distribution.items():
                key = (request_purchase.id, int(account))
                line_amount = (
                    requisition_line.price_total * (rate / 100.0)
                ) / (requisition_line.requisition_id.currency_rate or 1.0)
                reserved_mapping[key] += line_amount

        return True

    def _calculate_task_reserved(self, request_purchase, task, reserved_mapping):
        """Calculate reserved amounts based on confirmed vendor selections for a task."""
        confirmed_selections = task.rfq_selection_ids.filtered(
            lambda selection: selection.state in CONFIRMED_SELECTION_STATES)[:1]
        if not confirmed_selections:
            return False

        for order_line in confirmed_selections.mapped("po_id.order_line"):
            for account, rate in order_line.analytic_distribution.items():
                key = (request_purchase.id, int(account))
                line_amount = (
                    order_line.price_subtotal * (rate / 100.0)
                ) / (order_line.order_id.currency_rate or 1.0)
                reserved_mapping[key] += line_amount

        return True

    def _get_used_amount(self):
        """Calculate the actual amount consumed from this budget reservation.

        Aggregates analytic line amounts from:
        - Task-related analytic entries (procurement task costs)
        - Request purchase analytic entries (direct purchase costs)
        """
        self.ensure_one()

        # Collect all related analytic entries
        task_analytics = self.task_ids.analytic_line_ids
        request_analytics = self.request_purchase_id.analytic_line_ids
        all_analytics = task_analytics | request_analytics

        account_analytics = all_analytics.filtered(
            lambda line: line.account_id == self.account_id
        )

        # Sum amounts (negative for expenses) and return absolute value
        total_used = sum(account_analytics.mapped("amount"))
        return abs(total_used)

    @api.model
    def create(self, vals):
        if "request_purchase_id" in vals:
            request = self.env["request.purchase"].browse(vals["request_purchase_id"])
            vals.update(
                {
                    "user_id": request.user_id.id,
                    "company_id": request.company_id.id,
                    "name": request.name + " - Budget Reservation",
                    "date": request.issue_date,
                }
            )
        return super().create(vals)
