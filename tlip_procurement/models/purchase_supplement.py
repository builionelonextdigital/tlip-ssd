from collections import defaultdict
from itertools import groupby
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class PurchaseSupplement(models.Model):
    _name = "purchase.supplement"
    _inherit = ["purchase.agreement.base", "cr.mixin"]
    _description = "Purchase Supplement"

    state = fields.Selection(
        selection=[
            ("draft", "New"),
            ("wait", "Waiting for Approval"),
            ("approve", "Approved"),
            ("reject", "Rejected"),
            ("cancel", "Cancelled"),
            ("done", "Completed"),
        ],
        default="draft",
        tracking= True,
    )
    requisition_id = fields.Many2one("purchase.requisition", required=True)
    purchase_contract_name = fields.Char(
        related="requisition_id.name", readonly=True, string="Items"
    )
    purchase_contract_type_id = fields.Many2one(
        "purchase.contract.type",
        related="requisition_id.purchase_contract_type_id",
        readonly=True,
    )
    line_ids = fields.One2many(
        "purchase.supplement.line", "supplement_id", string="Purchase Items"
    )
    reason = fields.Text("Description")
    effective_date = fields.Date("Effective Date")
    summary_change_ids = fields.One2many(
        "purchase.summary.change", "purchase_supplement_id", string="Changes"
    )
    total_amount_untaxed = fields.Float(
        compute='_compute_total_amount', store=True, readonly=True)
    contract_appendix = fields.Boolean()
    company_id = fields.Many2one('res.company', string='Company', related='requisition_id.company_id', store=True)

    @api.depends("line_ids.price_total")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount_untaxed = sum(rec.line_ids.mapped("price_total"))

    def _get_difference_record_changes(self, current_record):
        summary_change_vals = super()._get_difference_record_changes(current_record)
        summary_change_vals += [
            Command.create(
                {
                    "name": change.name,
                    "current_value": change.current_value,
                    "new_value": change.new_value,
                    "bypass_create": True,
                }
            )
            for change in self.summary_change_ids
        ]

        return summary_change_vals

    def action_submit_changes(self):
        self.ensure_one()
        self._validate_submit_approval()
        self._check_budgets()

        summary_change_vals = self._get_difference_record_changes(
            self.requisition_id)
        wizard = self.env["purchase.summary.change.wizard"].create(
            [
                {
                    "purchase_supplement_id": self.id,
                    "change_line_ids": summary_change_vals,
                }
            ]
        )
        return {
            "name": _("Summary of changes"),
            "view_mode": "form",
            "view_id": self.env.ref(
                "tlip_procurement.purchase_summary_change_wizard_view_form"
            ).id,
            "view_type": "form",
            "res_model": "purchase.summary.change.wizard",
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def _validate_submit_approval(self):
        self.ensure_one()
        if not (self.effective_date and self.reason):
            raise UserError(
                _("Please select an effective date and provide a reason for the change.")
            )

        if not self.requisition_id.active or self.requisition_id.state != 'done':
            raise UserError(
                _("You can only create a purchase supplement for an active and completed purchase contract.")
            )

        # Validate that all lines have analytic distribution
        lines_without_distribution = self.line_ids.filtered(
            lambda line: not line.analytic_distribution
        )
        if lines_without_distribution:
            product_names = ", ".join(lines_without_distribution.mapped("product_id.name"))
            raise UserError(
                _(
                    "All purchase supplement lines must have analytic distribution. "
                    "The following products are missing analytic distribution: %s"
                ) % product_names
            )

        # Validate that supplement accounts must exist in requisition accounts
        supplement_accounts = self.line_ids.mapped('distribution_analytic_account_ids')
        requisition_accounts = self.requisition_id.line_ids.mapped('distribution_analytic_account_ids')

        if new_accounts := (supplement_accounts - requisition_accounts):
            account_names = ", ".join(new_accounts.mapped("name"))
            raise UserError(
                _("The following analytic accounts do not exist in the original requisition and cannot be used in the supplement: %s") % account_names
            )

    def _check_budgets(self):
        # Search opening budget year (only 1 opened at the same time)
        open_budget_year = self.env['budget.analytic.year'].search(
            [('state', '=', 'confirmed'), ('company_id', '=', self.company_id.id)], limit=1)
        if not open_budget_year:
            raise ValidationError('Cannot find the Budget Year. Please check!')

        account_mapping = defaultdict(float)
        self.line_ids.calculate_budget_on_account(account_mapping, self.currency_rate, is_original=False)
        self.requisition_id.line_ids.calculate_budget_on_account(account_mapping, self.requisition_id.currency_rate, is_original=True)

        for account_id, amount_diff in account_mapping.items():
            budget_line = open_budget_year.budget_line_year_ids.filtered_domain(
                [('account_id', '=', account_id)])
            if not budget_line:
                continue
            if float_compare(amount_diff, budget_line.remained_amount, 2) == 1:
                err_msg = f"""
                The amount of product/service has exceeded the remaining budget.

                - The amount related to budget code "{budget_line.account_id.name} - ID: {budget_line.account_id.id}" has exceeded the remaining budget.
                """
                raise ValidationError(err_msg)

    def _fields_tracking_change(self):
        return [
            "buyer_id",
            "buyer_street",
            "buyer_street_2",
            "buyer_district",
            "buyer_ward",
            "buyer_state_id",
            "buyer_country_id",
            "vendor_id",
            "vendor_code",
            "vendor_street",
            "vendor_street_2",
            "vendor_district",
            "vendor_ward",
            "vendor_state_id",
            "vendor_country_id",
            "vendor_vat",
            "quotation_no",
            "quotation_date",
            "total_amount_untaxed",
            "tax_rate",
            "note",
            "commence_date",
            "estimated_month",
            "complete_date",
            "delivery_time",
            "delivery_street",
            "delivery_street_2",
            "delivery_district_id",
            "delivery_ward_id",
            "delivery_state_id",
            "delivery_country_id",
            "guarantee_period",
            "payment_frequency",
            "payment_term_days",
            "payment_term_description",
            "buyer_legal_name",
            "buyer_legal_title",
            "buyer_legal_attoney_no",
            "buyer_legal_email",
            "buyer_legal_fax",
            "buyer_legal_phone",
            "buyer_legal_vat",
            "buyer_legal_beneficiary",
            "buyer_legal_account_number",
            "buyer_legal_bank_id",
            "vendor_legal_name",
            "vendor_legal_title",
            "vendor_legal_attoney_no",
            "vendor_legal_email",
            "vendor_legal_fax",
            "vendor_legal_phone",
            "vendor_legal_beneficiary",
            "vendor_legal_account_number",
            "vendor_legal_bank_id",
            "user_id",
            "contract_signer_id",
            "line_ids",
            "currency_id",
            "currency_rate",
        ]

    def _prepare_purchase_contract_vals(self):
        self.ensure_one()
        origin = self.requisition_id.original_contract_id or self.requisition_id
        vals = {
            "purchase_contract_type_id": self.requisition_id.purchase_contract_type_id.id,
            "name": self.requisition_id.name,
            "state": "done",
            "task_id": self.requisition_id.task_id.id,
            "final_contract": self.requisition_id.final_contract.id,
            "company_id": self.requisition_id.company_id.id,
            "original_contract_id": origin.id,
        }
        fields_vals = self._fields
        for field in self._fields_tracking_change():
            vals[field] = self.convert_value_to_updated_val(
                fields_vals[field], self[field]
            )

        vals["line_ids"] = [
            Command.create(
                {
                    "product_id": l.product_id.id,
                    "product_uom_id": l.product_uom_id.id,
                    "product_qty": l.product_qty,
                    "price_unit": l.price_unit,
                    "tax_rate": l.tax_rate,
                    "specification": l.specification,
                    "analytic_distribution": l.analytic_distribution,
                }
            )
            for l in self.line_ids
        ]
        return vals

    def _action_effective(self):
        self.ensure_one()
        vals = self._prepare_purchase_contract_vals()
        new_purchase_contract = self.env["purchase.requisition"].create(vals)
        old_purchase_contract = self.requisition_id
        # Check and update value of inprogress POs based on new Purchase Contract

        new_contract_msg = _("This procurement contract has been created from: ") + self._get_html_link()
        new_purchase_contract.message_post(body=new_contract_msg)

        supplement_msg = _("A new procurement contract has been created: ") + new_purchase_contract._get_html_link()
        self.message_post(body=supplement_msg)

        self._migrate_purchase_orders(old_purchase_contract, new_purchase_contract)

        procurement_tasks = self.env['procurement.task'].search([
            ('current_contract_id', '=', old_purchase_contract.id)])
        procurement_tasks.write({'current_contract_id': new_purchase_contract.id})

        # Archive old contract and complete the supplement
        old_purchase_contract.action_archive()
        self.action_complete()

    def _trigger_action_after_submit(self, request):
        res = super()._trigger_action_after_submit(request=request)
        self.write({"state": "wait"})
        return res

    def _trigger_action_approve(self):
        today = fields.Date.today()
        self.write(
            {
                "state": "approve",
            }
        )
        for record in self.filtered(lambda r: r.effective_date <= today):
            record._action_effective()

    def _trigger_action_refuse(self):
        self.write({"state": "reject"})

    def _migrate_purchase_orders(self, old_contract, new_contract):
        purchase_orders = old_contract.purchase_ids
        purchase_orders.write({'requisition_id': new_contract.id})

        inprogress_POs = purchase_orders.filtered(lambda po: po.state in ['draft', 'sent', 'cancel'])
        if inprogress_POs:
            new_updates = {}
            for new_line in new_contract.line_ids:
                new_updates[new_line.product_id.id] = new_line.price_unit
            # Update new contract to inprogress POs
            for orderline in inprogress_POs.mapped('order_line'):
                new_update = new_updates.get(orderline.product_id.id, False)
                # Check and update if new value is difference
                if new_update and float_compare(new_update, orderline.price_unit, 2) != 0:
                    orderline.write({'price_unit': new_update})

    @api.model
    def cron_activate_purchase_supplement(self):
        today = fields.Date.today()
        supplements = self.env["purchase.supplement"].search(
            [("effective_date", "<=", today), ("state", "=", "approve")]
        )
        for record in supplements:
            record._action_effective()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "name" not in vals:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "purchase.supplement"
                ) or _("/")
        return super().create(vals_list)

    def action_complete(self):
        self.write({"state": "done"})

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals and vals["state"] in ('wait', 'reject', 'cancel'):
            tasks = self.env["procurement.task"]
            for record in self:
                requisition_id = record.requisition_id
                if not requisition_id.active or requisition_id.state != 'done':
                    continue

                tasks |= requisition_id.task_id

            # We will trigger compute to update reserved budgets on requisition lines
            if budget_reserved_ids := self.env['budget.reserved'].search([('task_ids', 'in', tasks.ids)]):
                budget_reserved_ids._compute_budget_reserved_amount()

        return res


class PurchaseSupplementLine(models.Model):
    _name = "purchase.supplement.line"
    _inherit = "purchase.requisition.line"
    _description = "Purchase Supplement Line"

    supplement_id = fields.Many2one(
        "purchase.supplement", "Purchase Supplement",
        required=True, ondelete='cascade'
    )
    requisition_id = fields.Many2one(
        "purchase.requisition", string="Requisition", required=False
    )
