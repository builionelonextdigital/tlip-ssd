from odoo import _, api, fields, models
from odoo.tools import groupby
from odoo.exceptions import UserError

from collections import defaultdict


class ChooseVendorWizard(models.TransientModel):
    _name = 'create.rfq.wizard'
    _description = 'Choose vendor to create RFQ'

    task_id = fields.Many2one(
        comodel_name="procurement.task", required=True,
        string="Procurement Task"
    )
    vendor_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Suppliers",
        check_company=True,
        domain="[('vendor_state', '=', 'approved'), ('id', 'not in', existing_vendor_ids), ('is_blocked', '=', False)]",
        required=True
    )

    existing_vendor_ids = fields.Many2many(
        'res.partner', 'create_rfq_vendor_rel', 'wizard_id', 'vendor_id')

    def action_create_rfqs(self):
        orders = self.env["purchase.order"].create(
            self._prepare_purchase_order_vals())
        action = self.env['ir.actions.actions']._for_xml_id(
            'purchase.act_res_partner_2_purchase_order')
        action['domain'] = [('id', 'in', orders.ids)]
        action['context'] = {'create': 0}
        return action

    def _prepare_purchase_order_vals(self):
        company = self.task_id.company_id
        order_vals = {
            "user_id": self.task_id.user_id.id,
            "date_order": self.task_id.date_order,
            "order_line": self._prepare_purchase_order_line_vals(),
            "company_id": company.id,
            "origin": ", ".join(self.task_id.request_line_ids.request_id.mapped("name")),
            'task_id': self.task_id.id,
        }
        return [{
            'partner_id': vendor.id,
            'payment_term_id': vendor.with_company(company).property_supplier_payment_term_id.id,
            **order_vals
        } for vendor in self.vendor_ids]

    def _prepare_purchase_order_line_vals(self):
        order_line_vals = []
        PurchaseRequestLine = self.env["request.purchase.line"]
        for (product, product_uom), request_lines in groupby(self.task_id.request_line_ids.sorted(lambda l: (l.product_id.id, l.product_uom_id.id)), lambda l: (l.product_id, l.product_uom_id)):
            request_lines = PurchaseRequestLine.concat(*request_lines)
            qty_demand = sum(request_lines.mapped("qty_demand"))
            analytic_distribution = self._get_analytic_distribution(
                request_lines, qty_demand)
            order_line_vals.append((0, 0, {
                "product_id": product.id,
                "price_unit": max(request_lines.mapped("price_unit")),
                "product_qty": sum(request_lines.mapped("qty_demand")),
                "analytic_distribution": analytic_distribution,
                "product_uom": product_uom.id,
                "origin": ", ".join(request_lines.request_id.mapped("name")),
            }))
        return order_line_vals

    def _get_analytic_distribution(self, request_lines, total_qty_demand):
        analytic_distribution = defaultdict(int)
        for line in request_lines:
            analytic_distribution[line.analytic_account_id.id] += (
                total_qty_demand and (line.qty_demand / total_qty_demand * 100))
        return analytic_distribution
