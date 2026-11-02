from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentRfpLine(models.Model):
    """RFP selected on an inbound payment, with the amount allocated to it (O2C No. 1).

    The RFP may still be in draft (approved, not posted). It is posted and
    reconciled when the payment is confirmed, see
    ``account.payment._post_and_reconcile_rfp_lines``.
    """

    _name = "account.payment.rfp.line"
    _description = "Payment RFP Allocation"
    _order = "sequence, id"
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    payment_id = fields.Many2one(
        "account.payment", required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="payment_id.company_id", store=True)
    currency_id = fields.Many2one(related="payment_id.currency_id")
    move_id = fields.Many2one(
        "account.move",
        string="Request for Payment",
        required=True,
        ondelete="restrict",
        check_company=True,
        index=True,
    )
    move_state = fields.Selection(related="move_id.state", string="RFP Status")
    move_approval_state = fields.Selection(
        related="move_id.approval_state", string="RFP Approval State"
    )
    invoice_date = fields.Date(related="move_id.invoice_date")
    invoice_date_due = fields.Date(related="move_id.invoice_date_due")
    move_amount_total = fields.Monetary(
        related="move_id.amount_total", string="RFP Total", currency_field="currency_id"
    )
    move_amount_open = fields.Monetary(
        string="RFP Amount Due",
        compute="_compute_move_amount_open",
        currency_field="currency_id",
    )
    amount = fields.Monetary(
        string="Allocated Amount",
        required=True,
        currency_field="currency_id",
    )

    _sql_constraints = [
        (
            "payment_move_uniq",
            "unique(payment_id, move_id)",
            "An RFP can only be selected once on the same payment.",
        ),
    ]

    @api.depends("move_id.state", "move_id.amount_total", "move_id.amount_residual")
    def _compute_move_amount_open(self):
        for line in self:
            move = line.move_id
            # A draft RFP has no receivable entry yet: what is due is its total.
            line.move_amount_open = (
                move.amount_total if move.state == "draft" else move.amount_residual
            )

    @api.onchange("move_id")
    def _onchange_move_id(self):
        for line in self:
            if line.move_id and not line.amount:
                line.amount = line.move_amount_open

    @api.constrains("amount", "move_id")
    def _check_amount(self):
        for line in self:
            currency = line.currency_id or line.company_id.currency_id
            if currency.compare_amounts(line.amount, 0.0) <= 0:
                raise ValidationError(
                    _("The allocated amount for %s must be positive.", line.move_id.display_name)
                )
            if currency.compare_amounts(line.amount, line.move_amount_open) > 0:
                raise ValidationError(
                    _(
                        "The allocated amount for %(rfp)s cannot exceed its amount due (%(due)s).",
                        rfp=line.move_id.display_name,
                        due=line.move_amount_open,
                    )
                )
