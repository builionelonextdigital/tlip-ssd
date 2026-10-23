from datetime import timedelta

from odoo import api, fields, models, _, Command
from odoo.tools import formatLang, float_round


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    parent_move_line_id = fields.Many2one(
        'account.move.line', string='Parent Line Id', copy=False)


class AccountMove(models.Model):
    _inherit = "account.move"

    completion_minutes_document = fields.Binary('Completion Minutes')
    deposit_paid_amount = fields.Monetary(string='Total Deposit', readonly=False)

    def _compute_amount_in_words(self):
        wth_deposit_moves = self.filtered(lambda m: m.move_type == 'out_invoice' and m.deposit_paid_amount > 0 and m.currency_id)
        super(AccountMove, (self - wth_deposit_moves))._compute_amount_in_words()

        for record in wth_deposit_moves:
            digits = record.currency_id.decimal_places if self.currency_id else 0
            residual_amount = record.amount_residual - record.deposit_paid_amount
            record.amount_in_words_en = record.currency_id.with_context(lang='en_US').amount_to_text(
                float_round(residual_amount, digits)).capitalize().replace('dong', 'Vietnamese Dong')
            record.amount_in_words_vn = record.currency_id.with_context(lang='vi_VN').amount_to_text(float_round(residual_amount, digits)).capitalize().replace('dong', 'đồng')

    def _update_parent_move(self):
        if self.state == 'posted' and self.parent_move_id and self.parent_move_id.state == 'draft' and self.parent_move_id.move_type == 'out_invoice':
            for line in self.invoice_line_ids:
                parent_line_id = line.parent_move_line_id
                parent_line_id.update({
                    'quantity': 1 if self.invoice_type_code == 'leasing' else parent_line_id.quantity - line.quantity,
                    'date_from': line.date_to + timedelta(days=1) if self.invoice_type_code == 'leasing' and
                    parent_line_id.date_from and
                    line.date_to else False
                })

    def _prepare_request_invoice_values(self):
        invoice_line_ids = []
        for line in self.invoice_line_ids:
            line_vals = line.copy_data()
            if line_vals:
                line_vals[0].update({
                    'parent_move_line_id': line.id
                })
                invoice_line_ids.append(line_vals[0])
        return {
            'parent_move_id': self.id,
            'invoice_line_ids': [Command.create(line) for line in invoice_line_ids],
            'line_ids': []
        }

    def action_request_invoice_on_draft(self):
        if self.state == 'draft' and self.move_type == 'out_invoice':
            new_move = self.copy(self._prepare_request_invoice_values())
            action = {
                'name': _('Request Invoice'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': new_move.id,
            }
            return action

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for record in self:
            record._update_parent_move()
        return res

    # def _trigger_action_approve(self):
    #     super()._trigger_action_approve()
    #     self.filtered(
    #         lambda m: m.parent_move_id and m.parent_move_id.state == 'draft' and m.move_type == 'out_invoice').action_post()

    def _generate_report_payment_request(self):
        """Override to include deposit paid amount for request payment invoices."""
        vals = super(AccountMove, self)._generate_report_payment_request()
        
        # Check if this is a request payment invoice
        if self.move_type == 'out_invoice':
            paid_amount = self.deposit_paid_amount
            vals.update({
                'amount_residual': formatLang(self.env, float_round(self.amount_total - paid_amount, 0), digits=0),
                'paid_amount': formatLang(self.env, float_round(paid_amount, 0), digits=0)
            })

        return vals
