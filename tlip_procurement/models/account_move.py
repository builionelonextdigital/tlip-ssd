from odoo import models, fields, api, _
from odoo.tools import float_compare, formatLang
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    request_purchase_id = fields.Many2one('request.purchase', string='Request for Goods/Service', copy=False)
    einvoice_form_no = fields.Char(string='Form No')
    einvoice_serial = fields.Char(string='Serial')
    einvoice_no = fields.Char(string='No')
    einvoice_line_ids = fields.One2many('e.invoice.line', 'move_id', string='E-Invoice Lines')
    einvoice_subtotals = fields.Monetary(string='Untaxed Amount', compute='_compute_einvoice_total', store=True, currency_field='currency_id')
    einvoice_total = fields.Monetary(string='Total', compute='_compute_einvoice_total', store=True, currency_field='currency_id')
    budget_department_responsible_job_id = fields.Many2one('hr.job', check_company=True,
                                                           compute="_compute_budget_department_responsible",
                                                           compute_sudo=True,
                                                           store=True)

    @api.depends('request_purchase_id', 'line_ids.purchase_line_id.order_id', 'invoice_line_ids.analytic_distribution')
    def _compute_budget_department_responsible(self):
        for record in self:
            budget_department = record.request_purchase_id.budget_department_id.with_context(
                company_id=record.company_id.id)

            # Ensure 1 vendor bill linked with 1 purchase order
            purchase_id = record.line_ids.purchase_line_id.order_id[:1]
            requisition = purchase_id.requisition_id
            task = purchase_id.task_id

            budget_department_responsible_job = (
                budget_department.job_id or
                requisition.budget_department_responsible_job_id or
                task.budget_department_responsible_job_id
            )

            if not budget_department_responsible_job and record.is_request_payment:
                budget_department_responsible_job = (
                    record.line_ids.get_department_job_on_analytic_distribution(
                        record_name=record.name,
                        company_id=record.company_id.id
                    )
                )

            record.budget_department_responsible_job_id = budget_department_responsible_job

    @api.depends_context('lang')
    @api.depends('einvoice_line_ids.price_subtotal', 'einvoice_line_ids.price_total', 'currency_id', 'company_id')
    def _compute_einvoice_total(self):
        for move in self:
            if move.einvoice_line_ids:
                move.einvoice_subtotals = sum(move.einvoice_line_ids.mapped('price_subtotal'))
                move.einvoice_total = sum(move.einvoice_line_ids.mapped('price_total'))
            else:
                move.einvoice_subtotals = 0
                move.einvoice_total = 0

    def action_submit_approval(self):
        request_purchase = self.request_purchase_id
        if request_purchase and \
            request_purchase.invoice_status != 'no' and \
            self.approval_state == 'draft' and \
            float_compare(
                self.amount_untaxed, request_purchase.remaining_invoiced_amount,
                2
            ) > 0:
            raise ValidationError(_(
                'Total expense amount is exceeded request purchase amount (%s %s).'
                'Please check and try again' % (request_purchase.remaining_invoiced_amount, request_purchase.currency_id.symbol))
            )

        return super().action_submit_approval()

    def open_import_einvoice_wizard(self):
        self.ensure_one()
        return {
            'name': _('Import E-Invoice'),
            'res_model': 'import.einvoice.wizard',
            'view_mode': 'form',
            'context': {
                'default_move_id': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_copy_invoice_lines_to_einvoice(self):
        self.ensure_one()
        product_lines = self.invoice_line_ids.filtered(lambda line: line.display_type == 'product')
        if not product_lines:
            raise UserError(_("Please input Invoice Lines before copying to E-Invoice."))

        lines_vals = []
        for line in product_lines:
            einvoice_line_vals = line._prepare_einvoice_line_vals()
            lines_vals.append(einvoice_line_vals)

        self.env['e.invoice.line'].create(lines_vals)

    def _to_validate_with_reserved_amount(self, account):
        invoice_lines = self.invoice_line_ids
        request_purchases = invoice_lines.request_purchase_line_id.request_id
        procurement_tasks = invoice_lines.purchase_order_id.task_id
        budget_reserved = self.env['budget.reserved'].search([
            '|',
            ('request_purchase_id', 'in', request_purchases.ids),
            ('task_ids', 'in', procurement_tasks.ids),
            ('account_id', '=', account.id)
        ])
        return sum(budget_reserved.mapped('amount'))

    def _prepare_validation_msgs_approval(self, soft=True):
        validation_msgs = super()._prepare_validation_msgs_approval(soft=soft)
        validation_msgs.extend(self._validate_einvoice_lines())
        return validation_msgs

    def _validate_einvoice_lines(self):
        validation_msgs = []
        for move in self.filtered(lambda m: m.move_type in ('in_invoice', 'in_refund')):
            validation_msgs.extend(move._check_einvoice_totals_match())

            input_msgs = dict(form_no="Form No", serial="Serial", number="No")
            for field, label in input_msgs.items():
                if move.einvoice_line_ids and not all(move.einvoice_line_ids.mapped(field)):
                    validation_msgs.append(_("All E-Invoice Lines must have %s filled in.") % label)

        return validation_msgs

    def _check_einvoice_totals_match(self):
        self.ensure_one()
        validation_msgs = []
        if not self.einvoice_line_ids:
            validation_msgs.append(_("E-Invoice Lines are required."))
            return validation_msgs

        currency = self.currency_id
        einvoice_untaxed = sum(self.einvoice_line_ids.mapped('price_subtotal'))
        einvoice_tax = sum(self.einvoice_line_ids.mapped('price_tax'))
        einvoice_total = sum(self.einvoice_line_ids.mapped('price_total'))

        if (
            currency.compare_amounts(einvoice_untaxed, self.amount_untaxed) != 0
            or currency.compare_amounts(einvoice_tax, self.amount_tax) != 0
            or currency.compare_amounts(einvoice_total, self.amount_total) != 0
        ):
            validation_msgs.append(_(
                "E-Invoice totals do not match Invoice Lines. Please check Untaxed, Tax, and Total.\n"
                "E-Invoice:     Untaxed = %(eu)s | Tax = %(et)s | Total = %(eto)s\n"
                "Invoice Lines: Untaxed = %(iu)s | Tax = %(it)s | Total = %(ito)s",
                eu=formatLang(self.env, einvoice_untaxed, currency_obj=currency),
                et=formatLang(self.env, einvoice_tax, currency_obj=currency),
                eto=formatLang(self.env, einvoice_total, currency_obj=currency),
                iu=formatLang(self.env, self.amount_untaxed, currency_obj=currency),
                it=formatLang(self.env, self.amount_tax, currency_obj=currency),
                ito=formatLang(self.env, self.amount_total, currency_obj=currency),
            ))

        return validation_msgs


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    request_purchase_line_id = fields.Many2one('request.purchase.line')

    def _prepare_einvoice_line_vals(self):
        self.ensure_one()
        price_tax = self.price_total - self.price_subtotal

        return {
            'move_id': self.move_id.id,
            'invoice_issuer': self.move_id.partner_id.name or '',
            'tax_code': self.move_id.partner_id.vat or '',
            'invoice_date': self.move_id.invoice_date or fields.Date.today(),
            'goods_name': self.name or self.product_id.name or '',
            'product_uom': self.product_uom_id.name or '',
            'product_uom_qty': self.quantity,
            'price_unit': self.price_unit,
            'taxes_id': [(6, 0, self.tax_ids.ids)],
            'price_subtotal': self.price_subtotal,
            'price_tax': price_tax,
            'price_total': self.price_total,
            'form_no': '',
            'serial': '',
            'number': '',
        }
