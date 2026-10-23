# -*- coding: utf-8 -*-

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        lines_vals_list = super(AccountMove, self)._stock_account_prepare_anglo_saxon_out_lines_vals()
        for move in self:
            for line_vals in lines_vals_list:
                move = move.with_company(move.company_id)
                invoice_line = move.invoice_line_ids.filtered(lambda x: x.product_id.id == line_vals.get("product_id"))
                line = invoice_line[0] if invoice_line else False
                if line:
                    accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                    debit_interim_account = accounts['stock_output']
                    if line_vals.get("account_id") == debit_interim_account.id:
                        line_vals.update({'analytic_distribution': line.analytic_distribution})
        return lines_vals_list
