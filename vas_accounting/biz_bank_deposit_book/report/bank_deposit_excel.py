# -*- coding: utf-8 -*-
from odoo import models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import base64
import io
from urllib.request import Request, urlopen

class rp_bank_deposit_book_xlsx(models.AbstractModel):
    _name = 'report.biz_bank_deposit_book.rp_bank_deposit_book_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'rp_bank_deposit_book_xlsx'
    
    def generate_xlsx_report(self, workbook, data, o):
        self = self.with_context(lang=self.env.user.lang)
        table_border_head = {
            'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True, 
            'align': 'center','border':True,'bold':True
        }
        table_border_body = {'font_name': 'Times New Roman', 'font_size': 12, 'align': 'left', 'top': True, 'bottom': True,'left':True,'right': True}

        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman', 'font_size': 12,'valign':'vcenter','align': 'left','text_wrap': True}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)


        company = self.env.company
        sheet = workbook.add_worksheet("Sổ tiền ngân hàng")
        sheet.set_column(0,0,20)
        sheet.set_column(1,1,15)
        sheet.set_column(2,2,15)
        sheet.set_column(3,3,29)
        sheet.set_column(4,4,20)
        sheet.set_column(5,5,17)
        sheet.set_column(6,6,15)
        sheet.set_column(7,7,15)
        sheet.set_column(8,8,10)

        sheet.set_default_row(20)
        sheet.hide_gridlines(2)

        y_offset = 0
        
        sheet.merge_range(y_offset, 0, y_offset, 3, 'Đơn vị: %s' % company.name, get_format({'bold': True}))
        sheet.merge_range(y_offset, 4, y_offset, 8, 'Mẫu số: S08-DN', get_format({'bold': True,'align': 'center'}))
        y_offset +=1
        sheet.set_row(y_offset, 35)
        sheet.merge_range(y_offset, 0, y_offset, 3, 'Địa chỉ: %s' % self.get_company_address(company), get_format({'bold': True}))
        sheet.merge_range(y_offset, 4, y_offset, 8, '(Ban hành theo Thông tư số 200/2014/TT-BTC', get_format({'align': 'center'}))
        y_offset+=1
        
        sheet.merge_range(y_offset, 4, y_offset, 8, 'Ngày 22/12/2014 của Bộ Tài chính)', get_format({'align': 'center'}))
        y_offset+=2

        sheet.merge_range(y_offset, 0, y_offset, 8, 'SỔ TIỀN GỬI NGÂN HÀNG', get_format({'font_size': 16, 'bold': True, 'align': 'center'}))
        y_offset+=1

        sheet.merge_range(y_offset, 0, y_offset, 8, 'Nơi mở tài khoản giao dịch: %s' % (o.journal_id.bank_account_id.display_name  or ''), get_format({'align': 'center'}))
        y_offset+=1

        sheet.merge_range(y_offset, 0, y_offset, 8, 'Số hiệu tài khoản tại nơi gửi: %s' % (o.journal_id.bank_id.display_name  or ''), get_format({'align': 'center'}))
        y_offset+=2

        # Table head
        sheet.merge_range(y_offset,0, y_offset+1, 0, 'Ngày, tháng ghi sổ', get_format(table_border_head))
        sheet.merge_range(y_offset, 1, y_offset, 2,  'Chứng từ', get_format(table_border_head))
        sheet.write(y_offset+1, 1, 'Số hiệu', get_format(table_border_head))
        sheet.write(y_offset+1, 2, 'Ngày, tháng', get_format(table_border_head))
        sheet.merge_range(y_offset,3, y_offset+1, 3, 'Diễn giải', get_format(table_border_head))
        sheet.merge_range(y_offset,4, y_offset+1, 4, 'Tài khoản đối ứng', get_format(table_border_head))
        sheet.merge_range(y_offset, 5, y_offset, 7,  'Số tiền', get_format(table_border_head))
        sheet.write(y_offset+1, 5, 'Thu (Gửi vào)', get_format(table_border_head))
        sheet.write(y_offset+1, 6, 'Chi (Rút ra)', get_format(table_border_head))
        sheet.write(y_offset+1, 7, 'Còn lại', get_format(table_border_head))
        sheet.merge_range(y_offset,8, y_offset+1, 8, 'Ghi chú', get_format(table_border_head))
        y_offset +=2
        
        sheet.write(y_offset, 0, 'A',  get_format(table_border_head))
        sheet.write(y_offset, 1, 'B',  get_format(table_border_head))
        sheet.write(y_offset, 2, 'C',  get_format(table_border_head))
        sheet.write(y_offset, 3, 'D',  get_format(table_border_head))
        sheet.write(y_offset, 4, 'E',  get_format(table_border_head))
        sheet.write(y_offset, 5, '1',  get_format(table_border_head))
        sheet.write(y_offset, 6, '2',  get_format(table_border_head))
        sheet.write(y_offset, 7, '3',  get_format(table_border_head))
        sheet.write(y_offset, 8, 'F',  get_format(table_border_head))
        y_offset+=1

        data = self.get_lines(o)
        initial = self.get_initial_balance(o)
        remaining = initial

        sheet.write(y_offset, 0,'', get_format(table_border_body))
        sheet.write(y_offset, 1,'', get_format(table_border_body))
        sheet.write(y_offset, 2,'', get_format(table_border_body))
        sheet.write(y_offset, 3, '- Số dư đầu kỳ', get_format(table_border_body, {'bold': True}))
        sheet.write(y_offset, 4,'', get_format(table_border_body))
        sheet.write(y_offset, 5,'', get_format(table_border_body))
        sheet.write(y_offset, 6,'', get_format(table_border_body))
        sheet.write(y_offset, 7, self.format_float_number(remaining), get_format(table_border_body,{'align': 'right'}))
        sheet.write(y_offset, 8,'', get_format(table_border_body))
        y_offset+=1

        sheet.write(y_offset, 0,'', get_format(table_border_body))
        sheet.write(y_offset, 1,'', get_format(table_border_body))
        sheet.write(y_offset, 2,'', get_format(table_border_body))
        sheet.write(y_offset, 3, '- Số phát sinh trong kỳ', get_format(table_border_body, {'bold': True}))
        sheet.write(y_offset, 4,'', get_format(table_border_body))
        sheet.write(y_offset, 5,'', get_format(table_border_body))
        sheet.write(y_offset, 6,'', get_format(table_border_body))
        sheet.write(y_offset, 7,'', get_format(table_border_body))
        sheet.write(y_offset, 8,'', get_format(table_border_body))
        y_offset+=1

        for line in data['lines']:
            sheet.set_row(y_offset, 27)
            remaining = remaining + line['debit'] - line['credit'] 
            sheet.write(y_offset, 0, line['date'], get_format(table_border_body))
            sheet.write(y_offset, 1, line['move_name'], get_format(table_border_body))
            sheet.write(y_offset, 2, line['date'], get_format(table_border_body))
            sheet.write(y_offset, 3, line['name'] or '', get_format(table_border_body))
            sheet.write(y_offset, 4, line['cpt_code'], get_format(table_border_body))
            sheet.write(y_offset, 5, self.format_float_number(line['debit']), get_format(table_border_body,{'align': 'right'}))
            sheet.write(y_offset, 6, self.format_float_number(line['credit']), get_format(table_border_body,{'align': 'right'}))
            sheet.write(y_offset, 7, self.format_float_number(remaining), get_format(table_border_body,{'align': 'right'}))
            sheet.write(y_offset, 8, '', get_format(table_border_body))
            y_offset +=1

        sheet.write(y_offset, 0,'', get_format(table_border_body))
        sheet.write(y_offset, 1,'', get_format(table_border_body))
        sheet.write(y_offset, 2,'', get_format(table_border_body))
        sheet.write(y_offset, 3, '- Cộng số phát sinh trong kỳ', get_format(table_border_body, {'bold': True}))
        sheet.write(y_offset, 4,'', get_format(table_border_body))
        sheet.write(y_offset, 5, self.format_float_number(data['sum_debit']), get_format(table_border_body,{'align': 'right'}))
        sheet.write(y_offset, 6, self.format_float_number(data['sum_credit']), get_format(table_border_body,{'align': 'right'}))
        sheet.write(y_offset, 7,'', get_format(table_border_body))
        sheet.write(y_offset, 8,'', get_format(table_border_body))
        y_offset+=1


        end = initial + data['sum_debit'] - data['sum_credit']
        sheet.write(y_offset, 0,'', get_format(table_border_body, {'bottom': True}))
        sheet.write(y_offset, 1,'', get_format(table_border_body, {'bottom': True}))
        sheet.write(y_offset, 2,'', get_format(table_border_body, {'bottom': True}))
        sheet.write(y_offset, 3, '- Số dư cuối kỳ', get_format(table_border_body, {'bottom': True, 'bold': True}))
        sheet.write(y_offset, 4,'', get_format(table_border_body, {'bottom': True}))
        sheet.write(y_offset, 5,'', get_format(table_border_body, {'bottom': True}))
        sheet.write(y_offset, 6,'', get_format(table_border_body, {'bottom': True}))
        sheet.write(y_offset, 7, self.format_float_number(end), get_format(table_border_body, {'bottom': True, 'align': 'right'}))
        sheet.write(y_offset, 8,'', get_format(table_border_body, {'bottom': True}))
        y_offset+=2

        sheet.merge_range(y_offset, 0, y_offset, 8, '- Sổ này có ... trang, đánh số từ trang 01 đến trang...', get_format())
        y_offset+=1
        
        sheet.merge_range(y_offset, 0, y_offset, 8, '- Ngày mở sổ: ...', get_format())
        y_offset+=2
        sheet.merge_range(y_offset, 6, y_offset, 8, 'Ngày.....tháng.....năm.....', get_format({'italic': True, 'align': 'center'}))
        y_offset+=1
        sheet.merge_range(y_offset, 0, y_offset, 2, 'Người ghi sổ', get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 3, y_offset, 5, 'Kế toán trưởng', get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 6, y_offset, 8, 'Giám đốc', get_format({'bold': True, 'align': 'center'}))
        y_offset+=1
        sheet.merge_range(y_offset, 0, y_offset, 2, '(Ký, họ tên)', get_format({'italic': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 3, y_offset, 5, '(Ký, họ tên)', get_format({'italic': True, 'align': 'center'}))
        sheet.merge_range(y_offset, 6, y_offset, 8, '(Ký, họ tên, đóng dấu)', get_format({'italic': True, 'align': 'center'}))

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
                    for edeb in exit_debit:
                        initital = initital - edeb.debit +  edeb.credit

                        lines.append({
                            'initital': initital,
                            'date': edeb.date and edeb.date.strftime('%d/%m/%Y') or '',
                            'move_name': edeb.move_name or '',
                            'name': edeb.name or '',
                            'cpt_code': edeb.account_id.code,
                            'debit': edeb.credit,
                            'credit': edeb.debit,
                        })

                        sum_credit += edeb.debit
                        sum_debit += edeb.credit
                    continue

                if line.credit > 0 and not any(ec.credit > 0 for ec in exit_debit):
                    for ecre in exit_debit:
                        initital = initital - ecre.debit +  ecre.credit
                        lines.append({
                            'initital': initital,
                            'date': ecre.date and ecre.date.strftime('%d/%m/%Y') or '',
                            'move_name': ecre.move_name or '',
                            'name': ecre.name or '',
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
                'move_name': line.move_name or '',
                'name': line.name or '',
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