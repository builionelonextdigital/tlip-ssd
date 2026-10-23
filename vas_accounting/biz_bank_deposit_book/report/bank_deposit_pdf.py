# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models



class rp_bank_deposit_book_pdf(models.AbstractModel):
    _name = 'report.biz_bank_deposit_book.rp_bank_deposit_book_pdf'
    _description = 'Bank Deposit Book Report'
    
    def get_company_address(self, company_id):
        address = ''
        if company_id:
            if company_id.street:
                address = company_id.street
            if company_id.street2:
                address += len(address) and ', ' + company_id.street2 or company_id.street2
            if company_id.city:
                address += len(address) and ', ' + company_id.city or company_id.city
            if company_id.state_id:
                address += len(address) and ', ' + company_id.state_id.name or company_id.state_id.name
            if company_id.country_id:
                address += len(address) and ', ' + company_id.country_id.name or company_id.country_id.name
        return address

    def get_initial_balance(self, doc):
        domain = [('parent_state','=', 'posted')]
        if doc.from_date:
            domain += [('date','<', doc.from_date)]
        if doc.journal_id and doc.journal_id.default_account_id:
            domain += [('account_id','=', doc.journal_id.default_account_id.id)]

        initial = 0
        move_lines = self.env['account.move.line'].search(domain)
        for move in move_lines:
            initial += move.debit - move.credit

        return initial

    def get_lines(self, doc):
        domain = [('parent_state','=', 'posted')]
        if doc.from_date:
            domain += [('date','>=', doc.from_date)]

        if doc.to_date:
            domain += [('date','<=', doc.to_date)]

        if doc.journal_id:
            domain += [('journal_id','=', doc.journal_id.id)]

            if doc.journal_id.default_account_id:
                domain += [('account_id','=', doc.journal_id.default_account_id.id)]

        sum_credit  = sum_debit = 0
        move_lines = self.env['account.move.line'].search(domain,order="date asc")

        lines = []

        initital = self.get_initial_balance(doc)
        for line in sorted(move_lines,key=lambda x:(x.date,x.move_name)):
            move = line.move_id
            if len(move.line_ids) >= 3:
                exit_debit = move.line_ids.filtered(lambda x: x.id != line.id)
                if line.debit > 0 and not any(ed.debit > 0 for ed in exit_debit):
                    for edeb in sorted(exit_debit,key=lambda x:(x.date,x.name)):
                        initital = initital - edeb.debit +  edeb.credit

                        lines.append({
                            'initital': initital,
                            'date': edeb.date and edeb.date.strftime('%d/%m/%Y') or '',
                            'move_name': edeb.move_name,
                            'name': edeb.name,
                            'cpt_code': edeb.account_id.code,
                            'debit': edeb.credit,
                            'credit': edeb.debit,
                        })

                        sum_credit += edeb.debit
                        sum_debit += edeb.credit
                    continue
                if line.credit > 0 and not any(ec.credit > 0 for ec in exit_debit):
                    for ecre in sorted(exit_debit,key=lambda x:(x.date,x.name)):
                        initital = initital - ecre.debit +  ecre.credit
                        lines.append({
                            'initital': initital,
                            'date': ecre.date and ecre.date.strftime('%d/%m/%Y') or '',
                            'move_name': ecre.move_name,
                            'name': ecre.name,
                            'cpt_code': ecre.account_id.code,
                            'debit': ecre.credit,
                            'credit': ecre.debit,
                        })

                        sum_credit += ecre.debit
                        sum_debit += ecre.credit

                    continue

            initital = initital + line.debit -  line.credit
            lines.append({
                'initital': initital,
                'date': line.date and line.date.strftime('%d/%m/%Y') or '',
                'move_name': line.move_name,
                'name': line.name,
                'cpt_code': self.get_cpt_code(line),
                'debit': line.debit,
                'credit': line.credit,
            })

            sum_credit += line.credit
            sum_debit += line.debit


        return {
            'sum_credit': sum_credit,
            'sum_debit': sum_debit,
            'lines': lines
        }

    def get_cpt_code(self, line):
        code = ''
        if line.ctp_account_ids:
            codes = line.ctp_account_ids.filtered(lambda x: x.code)
            code = codes and ', '.join(codes.mapped('code')) or '' 
        return code

    def format_float_number(self, num):
        if not num:
            return 0

        number = float(num)
        if number % 1 == 0:
            return "{:,.0f}".format(number)
        else:
            number_format = "{:,.2f}".format(number).rstrip('0')
            numbers = number_format.split('.')
            return numbers[0] + ',' + numbers[1]

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'bank.deposit.book',
            'docs': self.env['bank.deposit.book'].browse(docids),
            'get_company_address': self.get_company_address,
            'get_initial_balance': self.get_initial_balance,
            'get_lines': self.get_lines,
            'get_cpt_code': self.get_cpt_code,
            'format_number': self.format_float_number
        }
