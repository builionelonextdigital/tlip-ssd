# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import html2plaintext

 
class rp_cash_book_pdf(models.AbstractModel):
    _name = 'report.biz_cash_book_money.rp_cash_book_pdf'
    _description = 'rp_cash_book_pdf'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        company = self.env.company
        currency_id = company.currency_id
        currency_name = currency_id.name or ''
        doc = self.env['cash.book'].browse(docids)
        options = data

        report_id = self.env['account.report'].browse(int(options['report_id']))
        from_date = options['date']['date_from'] if options.get('date') and options['date'].get('date_from') else ''
        to_date = options['date']['date_to'] if options.get('date') and options['date'].get('date_to') else ''
        account_name = ''
        account_ids = self.env['account.account']
        if options.get('account_ids'):
            account_ids = self.env['account.account'].browse(options['account_ids'])

        if from_date:
            from_date_date = datetime.strptime(from_date, "%Y-%m-%d")
            from_date = from_date_date.strftime('%d/%m/%Y')
        if to_date:
            to_date_date = datetime.strptime(to_date, "%Y-%m-%d")
            to_date = to_date_date.strftime('%d/%m/%Y')

        print_mode_self = report_id.with_context(no_format=True, print_mode=True, prefetch_fields=False)
        print_options = print_mode_self.get_options(previous_options=options)
        blines = report_id._filter_out_folded_children(print_mode_self._get_lines(print_options))

        col_stt = {
            'date': 1,
            'communication': 2,
            'partner_name': 3,
            'receipt': 4,
            'payment': 5,
            'explain': 6,
            'note': 7,
            'amount_currency': 8,
            'debit': 9,
            'credit': 10,
            'balance': 11,
        }
        if not self.env.user.has_group('base.group_multi_currency'):
            col_stt = {
                'date': 1,
                'communication': 2,
                'partner_name': 3,
                'receipt': 4,
                'payment': 5,
                'explain': 6,
                'note': 7,
                'debit': 8,
                'credit': 9,
                'balance': 10,
            }

        res = {}
        y_offset = 0

        group_accounts, parent_name = doc.get_group_account(blines)
        for parent_id, lines in group_accounts.items():  
            sum_debit = sum_credit = 0
            last_balance = 0

            for line in lines:
                columns = line['columns']

                vals = {}
                for x, column in enumerate(columns, start=1):
                    cell_type, cell_value = report_id._get_cell_type_value(column)
                    for key, stt in col_stt.items():
                        if stt == x:
                            vals[key] = cell_value

                if line.get("class") == 'o_account_reports_initial_balance':
                    account_name = ''
                    if len(group_accounts) >1 :
                        account_id = self.env['account.account'].browse(int(parent_id.split('~account.account~')[1]))
                        account_name = account_id and account_id.code or ''

                    res[y_offset] = {
                        'a': account_name,
                        'b': '',
                        'c': '',
                        'd': '',
                        'e': '- Số dư đầu kỳ',
                        'f': '',
                        'g': '',
                        'h': doc.format_float_number(vals['balance']),
                        'i': '',
                        'is_bold': True,
                    }
                    y_offset +=1      
                else:
                    if line.get('class', False) == 'total':
                        continue
                        
                    sum_debit += vals['debit'] and  float(vals['debit']) or 0
                    sum_credit += vals['credit'] and float(vals['credit']) or 0
                    last_balance = vals['balance']

                    res[y_offset] = {
                        'a': vals['date'] and vals['date'].strftime('%d/%m/%Y') or '',
                        'b': vals['date'] and vals['date'].strftime('%d/%m/%Y') or '',
                        'c': vals['receipt'] or '',
                        'd': vals['payment'] or '',
                        'e': vals['explain'],
                        'f': doc.format_float_number(vals['debit']),
                        'g': doc.format_float_number(vals['credit']),
                        'h': doc.format_float_number(vals['balance']),
                        'i': vals['note'] and html2plaintext(vals['note']) or '',
                        'is_bold': False,
                    }
                    y_offset += 1

            res[y_offset] = {
                'a': '',
                'b': '',
                'c': '',
                'd': '',
                'e': '- Cộng số phát sinh',
                'f': doc.format_float_number(sum_debit),
                'g': doc.format_float_number(sum_credit),
                'h': "",
                'i': '',
                'is_bold': True,
            }
            y_offset +=1      
            res[y_offset] = {
                'a': '',
                'b': '',
                'c': '',
                'd': '',
                'e': '- Số dư cuối kỳ',
                'f': '',
                'g': '',
                'h': doc.format_float_number(last_balance),
                'i': '',
                'is_bold': True,
            }
            y_offset +=1  

        return {
            'doc_ids': docids,
            'doc':doc,
            'get_user_company_address': doc.get_company_address(company),
            'account_type': doc.get_type_account(blines),
            'lines': res,
            'doc_model': 'cash.book',
        }