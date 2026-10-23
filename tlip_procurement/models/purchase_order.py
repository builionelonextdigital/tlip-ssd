from datetime import date

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_order = fields.Boolean()
    task_id = fields.Many2one(
        comodel_name="procurement.task", readonly=True,
        string="Procurement Task"
    )
    select_bidding = fields.Selection(related="task_id.select_bidding")
    is_advance_enabled = fields.Boolean(related="task_id.is_advance_enabled", store=True, readonly=False)   #Todo: this field should not be store, we make it store for importing data purpose
    payment_term_desc = fields.Text(string="Payment Term Description")
    other_condition = fields.Text(string="Other Condition")
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[('is_blocked', '=', False)]
    )
    requirement_line_ids = fields.One2many(
        'request.purchase.requirement.line', 'purchase_id')
    evaluation_survey_ids = fields.One2many("evaluation.survey", "po_id")
    development_project_id = fields.Many2one('development.project')
    development_phase_id = fields.Many2one('development.phase', string="Phase")
    payment_ids = fields.One2many('account.payment', 'purchase_order_id')
    amount_residual = fields.Monetary(compute='_compute_amount_residual')
    currency_rate = fields.Float(default=1.0, readonly=False)

    @api.constrains('currency_rate')
    def _check_currency_rate(self):
        for record in self:
            if record.currency_id != record.company_id.currency_id and float_compare(record.currency_rate, 1.0, 2) == 0:
                raise UserError(_("Please input currency rate"))

    def _compute_currency_rate(self):
        for order in self:
            order.currency_rate = order.currency_rate

    def _compute_amount_residual(self):
        for record in self:
            paid_amount = sum(record.payment_ids.filtered(lambda r: r.approval_state not in ('draft', 'rejected')).mapped('amount'))
            tax_amount = sum(record.invoice_ids.filtered(lambda inv: (inv.state == 'posted' or inv.accounting_approval_state == 'approved') \
                            ).mapped('amount_tax'))
            record.amount_residual = record.amount_total - paid_amount + tax_amount

    @api.depends("task_id", "request_purchase_id")
    def action_generate_evaluation_survey(self):
        self.ensure_one()
        if not self.evaluation_survey_ids:
            survey_vals = self._prepare_evaluation_survey_vals()
            self.env["evaluation.survey"].create(survey_vals)
        return self._action_view_evaluation_survey()

    def _prepare_picking(self):
        storable_lines = self.order_line.filtered(lambda line: line.product_id.type == 'consu' and line.product_id.is_storable)
        consumable_lines = self.order_line.filtered(lambda line: line.product_id.type == 'consu' and not line.product_id.is_storable)

        storable_picking_vals = super()._prepare_picking()
        storable_picking_vals.update({
            "partner_id": self.partner_id.id,
            "buyer_id": self.requisition_id.buyer_id.id or self.company_id.partner_id.id,
            "user_id": self.user_id.id,
        })
        picking_vals = [storable_picking_vals]
        if consumable_lines:
            consumable_picking_vals = storable_picking_vals.copy()
            consumable_picking_vals['for_storable_products'] = False
            picking_vals.append(consumable_picking_vals)

        return picking_vals

    def _action_view_evaluation_survey(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "tlip_evaluation.evaluation_survey_action")
        if len(self.evaluation_survey_ids) == 1:
            context = dict(self.env.context) or {}
            action.update({
                'views': [(self.env.ref('tlip_evaluation.view_evaluation_survey_form').id, 'form')],
                'target': 'current',
                'res_id': self.evaluation_survey_ids[0].id,
                'context': context
            })
        else:        
            action["domain"] = [("po_id", "=", self.id)]

        return action

    def _prepare_evaluation_survey_vals(self):
        self.ensure_one()
        evaluation_type = self.env.context.get("default_evaluation_type", False)
        return {
            "evaluation_date": fields.Date.today(),
            "partner_id": self.partner_id.id,
            "po_id": self.id,
            "evaluation_type": evaluation_type,
        }

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals['is_request_payment'] = True
        return vals

    def action_view_invoice(self, invoices=False):
        action = self.env['ir.actions.actions']._for_xml_id('tlip_account.action_invoice_payment_request')
        form_res = self.env.ref('tlip_account.view_invoice_request_payment_form', False)

        if len(self.invoice_ids) == 1:
            action.update({
                'views': [(form_res and form_res.id or False, 'form')],
                'res_id': self.invoice_ids.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', self.invoice_ids.ids)],
            })

        action.update({'invoice_ids': invoices.ids if invoices else False})
        return action

    def action_view_account_payments(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('tlip_account.action_outbound_payment_request_payment')
        action.update({'create': False})
        if len(self.payment_ids) == 1:
            action.update({
                'views': [(self.env.ref('tlip_account.view_payment_request_payment_form').id, 'form')],
                'target': 'current',
                'res_id': self.payment_ids.id,
            })
        else:
            action.update({
                'domain':  [('purchase_order_id', '=', self.id)],
            })
        return action

    def action_request_payment(self):
        self.ensure_one()
        invoices = self.invoice_ids.filtered(lambda inv: 
            (inv.state == 'posted' or inv.accounting_approval_state == 'approved') \
            and inv.amount_residual != 0
        )
        if self.date_approve and self.date_approve.date() < date(2026, 2, 28):
            migration_moves = self.env['account.move'].get_migration_moves(
                move_types=['in_invoice', 'in_refund'],
                company_id=self.company_id.id,
                partner_id=self.partner_id.id
            )
            invoices |= migration_moves

        return {
            'name': _("Request for Payment"),
            'type': 'ir.actions.act_window',
            'res_model': 'procurement.make.payment',
            'target': 'new',
            'views': [(False, 'form')],
            'context': {'default_purchase_order_id': self.id, 
                        'default_available_bill_ids': [(6, 0, invoices.ids)],
                        'default_task_id': self.task_id.id}
        }

    def button_confirm(self):
        for rec in self:
            if rec.requisition_id and float_compare(rec.amount_untaxed, rec.requisition_id.remaining_amount, 2) > 0:
                raise ValidationError(_(f'{rec.name} amount exceeds {rec.requisition_id.name} remaining amount. Please check and try again'))
                        
            if not rec.order_line:
                raise UserError(_("Please add at least one product line to the purchase order."))

        return super().button_confirm()

    @api.model_create_multi
    def create(self, vals_list):
        IrSequence = self.env['ir.sequence'].with_context(month_sequence=True).sudo()
        for vals in vals_list:
            if vals.get('name', 'New') == 'New' and 'is_order' in vals:
                po_sequence_code = 'purchase.order.po' if vals.get('is_order', False) else 'purchase.order.rfq'
                vals['name'] = IrSequence.next_by_code(po_sequence_code) or '/'
        return super().create(vals_list)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_categ_id = fields.Many2one(related='request_line_id.product_categ_id', string="Category")
    warranty = fields.Char()
    origin = fields.Char(string="Source Document")
    request_line_id = fields.Many2one('request.purchase.line')
    project_id = fields.Many2one(related='request_line_id.project_id')
    development_phase_id = fields.Many2one(related='request_line_id.development_phase_id')
    available_request_line_ids = fields.Many2many('request.purchase.line', compute='_compute_available_request_line_ids')
    specification = fields.Text(string='Specification')

    def unlink(self):
        if self.order_id.task_id:
            raise UserError(_("Do not allow to delete Products line."))
        return super().unlink()

    def _prepare_stock_moves(self, picking):
        picking = picking.filtered(lambda p: p.state not in ('done', 'cancel') and p.for_storable_products == self.product_id.is_storable)[:1]
        return super()._prepare_stock_moves(picking)

    @api.depends('order_id.task_id')
    def _compute_available_request_line_ids(self):
        for record in self:
            record.available_request_line_ids = [(6, 0, record.order_id.task_id.request_line_ids.ids)]

    @api.onchange('request_line_id')
    def _onchange_request_line(self):
        if self.request_line_id.analytic_account_id:
            self.analytic_distribution = {self.request_line_id.analytic_account_id.id: 100}
    
    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        res.update({'analytic_distribution': self.analytic_distribution})
        return res
