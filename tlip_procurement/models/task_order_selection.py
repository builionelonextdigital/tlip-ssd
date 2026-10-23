import json

from odoo import fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError, ValidationError


class TaskOrderSelection(models.Model):
    _name = "task.order.selection"
    _inherit = ["mail.thread", "mail.activity.mixin", "approval.matrix.mixin"]
    _description = "Task Order Selection"

    task_id = fields.Many2one(
        comodel_name="procurement.task",
        readonly=True,
        string="Procurement Task",
        required=True,
    )
    po_id = fields.Many2one(
        comodel_name="purchase.order",
        required=True,
        string="Proposed RFQ",
    )
    vendor_id = fields.Many2one(related="po_id.partner_id", store=True)
    copy_fs_file = fields.Binary(
        string="Copy FS attachment", related="vendor_id.copy_fs_file"
    )
    copy_fs_filename = fields.Char(related="vendor_id.copy_fs_filename")
    copy_client_file = fields.Binary(
        string="Copy Client list", related="vendor_id.copy_client_file"
    )
    copy_client_filename = fields.Char(
        related="vendor_id.copy_client_filename")
    site_check_file = fields.Binary(
        string="Site Check report", related="vendor_id.site_check_file"
    )
    site_check_filename = fields.Char(related="vendor_id.site_check_filename")
    result_site_check = fields.Char(
        "Result of Site Check", related="vendor_id.result_site_check"
    )
    other_notes = fields.Char("Other notes", related="vendor_id.other_notes")
    fs_annual_sales = fields.Float(related="vendor_id.fs_annual_sales")
    fs_annual_pat = fields.Float(related="vendor_id.fs_annual_pat")
    fs_total_assets = fields.Float(related="vendor_id.fs_total_assets")
    currency_id = fields.Many2one(related="po_id.currency_id")
    company_id = fields.Many2one(related='task_id.company_id')
    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id', readonly=True,
    )
    amount_untaxed = fields.Monetary(compute='_compute_amount_untaxed', currency_field="company_currency_id",)
    reason = fields.Text()

    requisition_id = fields.Many2one("purchase.requisition")
    state = fields.Selection(
        selection=[
            ("waiting_confirm", "Waiting for Confirmation"),
            ("waiting_approval", "Waiting Approval"),
            ("confirmed", "Confirmed"),
            ("rejected", "Rejected"),
            ("canceled", "Canceled"),
        ],
        string="Status",
        default="waiting_confirm",
    )
    show_preference_check = fields.Boolean()
    bypass_contract = fields.Boolean()
    confirm_wizard_vals = fields.Text(
        help="For internal use only, type dict contains the values of the confirm wizard (reason, bypass_contract)"
    )

    def _compute_amount_untaxed(self):
        for record in self:
            if record.currency_id == record.company_currency_id:
                record.amount_untaxed = record.po_id.amount_untaxed
            else:
                record.amount_untaxed = record.po_id.amount_untaxed * record.po_id.currency_rate

    def button_confirm_order_selection(self):
        self.ensure_one()
        self._validate_confirm_order_selection()
        # Always reset, in case user previously cancel and re-select.
        self.task_id.rfq_selection_ids._reset_confirm_wizard()
        bypass_amount_maximum = self.env.company.purchase_contract_bypass_maximum
        disable_bypass_contract = False
        if float_compare(self.amount_untaxed, bypass_amount_maximum, 2) == 1:
            disable_bypass_contract = True
        return {
            'type': 'ir.actions.act_window',
            'name': _("Confirm"),
            'res_model': 'task.rfq.confirm.wizard',
            'views': [(self.env.ref('tlip_procurement.task_rfq_confirm_wizard_view_form').id, 'form')],
            'target': 'new',
            'context': {
                'default_rfq_selection_id': self.id,
                'disable_bypass_contract': disable_bypass_contract
            }
        }

    def action_confirm_preference_check(self):
        self.ensure_one()
        if self.amount_untaxed >= self.env.company.minimum_preference_check_amount:
            vendor_id = self.vendor_id.id
            existed_contract = self.env["purchase.requisition"].search(
                [("vendor_id", "=", vendor_id), ("state", "=", "approve")]
            )
            existed_payment = self.env["account.payment"].search(
                [("partner_id", "=", vendor_id), ("state", "=", "paid")]
            )
            
            if not existed_contract and not existed_payment:
                self.update_confirm_wizard_vals({"show_preference_check": True})
                action = self.env["ir.actions.act_window"]._for_xml_id(
                    "tlip_procurement.preference_check_action"
                )
                action.update(
                    {
                        "target": "new",
                        "res_id": self.id
                    }
                )
                return action
        return self.action_submit_approval()

    def action_confirm(self):
        self.ensure_one()
        if not self.confirm_wizard_vals:
            return

        confirm_wizard_vals = self._extract_confirm_wizard_vals()
        if confirm_wizard_vals.get("bypass_contract") and not self.env.context.get(
            "approval_submission"
        ):
            # Bypass contract and proceed to approved state
            task = self.task_id
            task.write({'state': 'approved'})
            return self.with_context(
                approval_submission=True).action_confirm()

        vals = {
            "state": "confirmed",
            "show_preference_check": confirm_wizard_vals.get("show_preference_check"),
        }
        if not confirm_wizard_vals.get("bypass_contract"):
            purchase_requisition = self.action_create_requisition_agreement()
            vals.update({"requisition_id": purchase_requisition.id})
            self.task_id.write({'state': 'contract_review'})

        self._convert_active_product()
        self.write(vals)
        rfq_selections = self.task_id.rfq_selection_ids
        rfq_selections.action_cancel(
            domain=[("state", "=", "waiting_confirm")]
        )
        rfq_selections._reset_confirm_wizard()

    def _convert_active_product(self):
        self.ensure_one()
        po = self.po_id
        for order_line in po.order_line.filtered(lambda l: l.product_id.categ_id == self.env.ref('tlip_procurement.product_category_rfq') and not l.product_id.purchase_ok):
            order_line.product_id.write({'categ_id': order_line.request_line_id.product_categ_id.id,
                                         'purchase_ok': True})

    def action_create_requisition_agreement(self):
        self.ensure_one()
        requisition_vals = self._prepare_purchase_requisition_vals()
        purchase_requisition = self.env["purchase.requisition"].create(
            requisition_vals)
        task = self.task_id
        po = self.po_id
        order_lines = po.order_line
        po_currency_id = po.currency_id
        for request_line in task.request_line_ids:
            request_line.write({
                'contract_total': sum(order_lines.filtered(lambda l: l.request_line_id == request_line).mapped('price_subtotal')),
                'contract_currency_id': po_currency_id.id,
            })
        return purchase_requisition

    def update_confirm_wizard_vals(self, addon_vals={}):
        self.ensure_one()
        confirm_wizard_vals = self._extract_confirm_wizard_vals()
        confirm_wizard_vals.update(addon_vals)
        self.write({"confirm_wizard_vals": json.dumps(confirm_wizard_vals)})

    def _prepare_purchase_requisition_vals(self):
        po = self.po_id
        task_id = self.task_id
        buyer_id = task_id.company_id.partner_id.id
        vendor_id = po.partner_id.id
        return {
            "user_id": task_id.user_id.id,
            "reference": task_id.name,
            "task_id": task_id.id,
            "vendor_id": vendor_id,
            "buyer_id": buyer_id,
            "company_id": po.company_id.id,
            "currency_id": po.currency_id.id,
            "currency_rate": po.currency_rate,
            "line_ids": self._prepare_purchase_requisition_line_vals(),
            "purchase_contract_type_id": task_id.purchase_contract_type_id.id,
            "task_ids": [(6, 0, task_id.ids)]
        }

    def _prepare_purchase_requisition_line_vals(self):
        return [
            (
                0,
                0,
                {
                    "product_id": line.product_id.id,
                    "price_unit": line.price_unit,
                    "product_qty": line.product_qty,
                    "analytic_distribution": line.analytic_distribution,
                    "product_uom_id": line.product_uom.id,
                    "product_description_variants": line.name,
                    "specification": line.name
                },
            )
            for line in self.po_id.order_line
        ]

    def _reset_confirm_wizard(self):
        self.write({"confirm_wizard_vals": False})

    def _extract_confirm_wizard_vals(self):
        self.ensure_one()
        return json.loads(self.confirm_wizard_vals) if self.confirm_wizard_vals else {}

    # Handle approval flow for selection vendor
    def action_submit_approval(self):
        action = super().action_submit_approval()
        if action and isinstance(action, dict) and action.get('type') == 'ir.actions.act_window':
            action["context"]["default_name"] = _(
                f"Approval Request for Select Vendor {self.vendor_id.name} from Procurement Task {self.task_id.name}"
            )
        return action

    def action_cancel(self, domain=[]):
        domain = domain or []
        self.filtered_domain(domain).write({"state": "canceled"})

    def _trigger_action_approve(self):
        return self.action_confirm()

    def _trigger_action_refuse(self):
        self.write({
            'state': 'rejected',
            'reason': False,
            'confirm_wizard_vals': False,
        })

    def _trigger_action_cancel(self):
        self._reset_selection_vendor()

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        confirm_wizard_vals = self._extract_confirm_wizard_vals()
        self.write({
            'state': 'waiting_approval',
            "reason": confirm_wizard_vals.get("reason"),
            "bypass_contract": confirm_wizard_vals.get("bypass_contract", False),
        })
        task = self.task_id
        task.write({'approval_request_id': request.id})
        model_id = self.env['ir.model']._get(task._name).id
        # switch activities to procurement task
        self.activity_ids.write({'res_model_id': model_id, 'res_id': task.id})
        rfq_selections = task.rfq_selection_ids
        rfq_selections.action_cancel(domain=[('state', '=', 'waiting_confirm')])
        return result

    def action_reset_approval(self):
        self.ensure_one()
        "Approval State: Rejected | Withdrawn -> Draft"
        self.task_id.rfq_selection_ids.write({"state": "waiting_confirm"})
        activity_type_id = self.env.ref(
            'approvals.mail_activity_data_approval').id
        self.task_id.activity_ids.filtered(
            lambda ac: ac.activity_type_id.id == activity_type_id).unlink()

    def _trigger_action_withdraw(self, reason: str):
        self._reset_selection_vendor()
        super()._trigger_action_withdraw(reason)

    def _reset_selection_vendor(self):
        rfq_selections = self.task_id.rfq_selection_ids
        rfq_selections.write({'state': 'waiting_confirm'})

    def _validate_confirm_order_selection(self):
        for rec in self:
            if rec.amount_untaxed > rec.task_id.amount_total:
                raise UserError(
                    _("Amount of selected RFQ must not exceed the total amount of Request Items.")
                )
