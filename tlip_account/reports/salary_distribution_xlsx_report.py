# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

cols = {
    'partner_ref': 0,
    'partner_name': 1,
    'description': 2,
    'request_payment_number': 3,
    'date': 4,
    'due_date': 5,
    'invoice_no': 6,
    'issue_date': 7,
    'currency': 8,
    'request_payment_amount': 9,
    'payment_amount': 10,
    'payment_date': 11,
    'outstanding_amount': 12,
    'overdue_amount': 13,
    'overdue_date': 14,
    'direct_debit': 15
}


class DebitAndCreditControlListReport(models.AbstractModel):
    _name = 'report.tlip_account.report_salary_distribution_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Salary Distribution Report'

    def get_company_address(self, company):
        address = ''
        if company:
            if company.street:
                address += company.street
            if company.street2:
                address += len(address) > 0 and ', ' + \
                    company.street2 or company.street2
            if company.city:
                address += len(address) > 0 and ', ' + \
                    company.city or company.city
            if company.state_id:
                address += len(address) > 0 and ', ' + \
                    company.state_id.name or company.state_id.name
            if company.country_id:
                address += len(address) > 0 and ', ' + \
                    company.country_id.name or company.country_id.name
        return address

    def generate_xlsx_report(self, workbook, data, o):
        self = self.with_context(lang=self.env.user.lang)

        table_border_head = {
            'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True,
            'align': 'center', 'border': True, 'bold': True
        }
        table_border_body = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'border': True, 'align': 'left',
                                                'right': 1, 'text_wrap': True})
        table_border_body_number = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'border': True, 'align': 'right',
                                                        'num_format': '#,###', 'right': 1})
        table_border_subtotal_number = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'border': True, 'align': 'right',
                                                        'num_format': '#,###', 'right': 1, 'bold': True})

        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman',
                            'font_size': 12, 'valign': 'vcenter', 'align': 'left'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)

        sheet = workbook.add_worksheet("Sheet 1")
        # sheet.hide_gridlines(2)
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 15)
        sheet.set_column(13, 13, 15)
        sheet.set_column(14, 14, 15)
        sheet.set_column(15, 15, 15)
        sheet.set_column(16, 16, 15)
        sheet.set_column(17, 17, 15)

        company_id = self.env.company
        y_offset = 0
        company_id = self.env.company
        sheet.write(y_offset, 0, '%s' % (
                    company_id.name), get_format({'bold': True}))
        y_offset += 1
        sheet.write(y_offset, 0, 'Địa chỉ: %s' % (
            self.get_company_address(company_id)), get_format({'bold': True}))
        y_offset += 2
        sheet.merge_range(y_offset, 0, y_offset, 10, 'MONTHLY SALARY DISTRIBUTION REPORT/ BÁO CÁO PHÂN BỔ LƯƠNG THÁNG', get_format(
            {'font_size': 16, 'bold': True, 'align': 'center'}))
        y_offset += 1
        sheet.merge_range(y_offset, 0, y_offset, 10, 'Từ ngày: %s   Đến ngày: %s' % (o.from_date, o.to_date), get_format(
            {'font_size': 12, 'bold': True, 'align': 'center'}))
        y_offset += 2
        # header table
        sheet.merge_range(y_offset, 0, y_offset + 1, 0, 'STT/ No',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 1, y_offset + 1, 1, 'Chỉ tiêu/ Item',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 2, y_offset + 1, 2, 'Mã ngân sách/ Budget Code',
                          get_format(table_border_head))
        sheet.write(y_offset, 3, 'TK Có/\nCredit Account',
                    get_format({
                        'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True,
                        'align': 'right', 'border': True, 'bold': True
                    }))
        sheet.write(y_offset + 1, 3, 'TK Nợ/\nDebit Account',
                    get_format({
                        'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True,
                        'align': 'left', 'border': True, 'bold': True
                    }))
        sheet.merge_range(y_offset, 4, y_offset + 1, 4, 'Tổng lương/ Salary Amount',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 5, y_offset + 1, 5, 'Phụ cấp khác/ Other Allowance',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 6, y_offset + 1, 6, 'Cộng khác/ Additional',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 7, y_offset + 1, 7, 'BHXH-Com/ Social Ins.',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 8, y_offset + 1, 8, 'BHXH-Staff/ Social Ins.',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 9, y_offset + 1, 9, 'BHYT-Com/ Heath Ins.',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 10, y_offset + 1, 10, 'BHYT-Staff/ Heath Ins.',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 11, y_offset + 1, 11, 'BHTN-Comm/ Unemployment Ins.',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 12, y_offset + 1, 12, 'BHTN-Staff/ Unemployment Ins.',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 13, y_offset + 1, 13, 'KPCD-Staff/ Trade Union',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 14, y_offset + 1, 14, 'KPCD-Com/ Trade Union',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 15, y_offset + 1, 15, 'Thuê TNCN/ PIT',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 16, y_offset + 1, 16, 'Khấu trừ khác/ Deduction',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 17, y_offset + 1, 17, 'Phải trả người lao động/ Payable to employees',
                          get_format(table_border_head))
        y_offset += 2
        sheet.write(y_offset, 0, '',
                    get_format(table_border_head))
        sheet.write(y_offset, 1, '',
                    get_format(table_border_head))
        sheet.write(y_offset, 2, '',
                    get_format(table_border_head))
        sheet.write(y_offset, 3, '',
                    get_format(table_border_head))
        sheet.write(y_offset, 4, '3341',
                    get_format(table_border_head))
        sheet.write(y_offset, 5, '3341',
                    get_format(table_border_head))
        sheet.write(y_offset, 6, '33881',
                    get_format(table_border_head))
        sheet.write(y_offset, 7, '3383',
                    get_format(table_border_head))
        sheet.write(y_offset, 8, '3383',
                    get_format(table_border_head))
        sheet.write(y_offset, 9, '3384',
                    get_format(table_border_head))
        sheet.write(y_offset, 10, '3384',
                    get_format(table_border_head))
        sheet.write(y_offset, 11, '3386',
                    get_format(table_border_head))
        sheet.write(y_offset, 12, '3386',
                    get_format(table_border_head))
        sheet.write(y_offset, 13, '3382',
                    get_format(table_border_head))
        sheet.write(y_offset, 14, '3382',
                    get_format(table_border_head))
        sheet.write(y_offset, 15, '3335',
                    get_format(table_border_head))
        sheet.write(y_offset, 16, '13881',
                    get_format(table_border_head))
        sheet.write(y_offset, 17, '3341',
                    get_format(table_border_head))
        y_offset += 1
        values = self.get_lines(o)
        account_ids = list(set([val.get('debit_account_id') for val in values])) + \
            list(set([val.get('credit_account_id') for val in values]))
        account_dict = {}
        accounts = self.env['account.account'].browse(account_ids)
        for acc in accounts:
            account_dict[acc.id] = acc.code
        budget_ids = list(set([val.get('budget_code_id')
                          for val in values if val.get('budget_code_id')]))
        budget_dict = {}
        budgets = self.env['budget.code'].browse(budget_ids)
        for budget in budgets:
            budget_dict[budget.id] = {'name': budget.name, 'code': budget.code}
        row = y_offset
        # 1. Định nghĩa bộ lọc Budget cho Phần I và Phần II
        sec_1_budgets = ['OM01-01-01', 'OM01-01-04', 'OB04-01-01', 'TA01-03-01']
        sec_2_budgets = ['OM01-02-01', 'OM01-02-03', 'TA01-03-02']
        sec_3_budgets = [
            'OM01-01-02', 'OM01-02-01', 'OB04-01-01', 'OM01-02-03', 
            'MF02-01-01', 'PW01-01-01', 'PW02-01-01', 'WB01-01-01', 
            'WB02-01-01', 'WB03-01-01', 'WB04-01-01', 'MF02-01-02', 
            'PW01-01-02', 'PW02-01-02', 'WB01-01-02', 'WB02-01-02', 
            'WB03-01-02', 'WB04-01-02', 'MF01-01-01', 'OB03-01-01', 'OM02-04-07'
        ]
        grand_total_usd = {}
        grand_total_vnd = {}

        # 2 & 3. Hàm map tài khoản vào đúng cột theo các Rule
        def get_col_idx(section, debit_code, credit_code):
            # Các khoản thu nhập / khấu trừ cố định
            if credit_code == '3341': return 4  # Tổng lương
            if credit_code == '33881': return 6 # Cộng khác
            if credit_code == '3335': return 15 # Thuế TNCN
            if credit_code == '13881': return 16 # Khấu trừ khác

            # Rule 3: Chỉ tiêu không phân biệt budget, nếu Nợ 3341 -> auto ghi vào cột Staff
            if debit_code == '3341':
                if credit_code == '3383': return 8
                if credit_code == '3384': return 10
                if credit_code == '3386': return 12
                if credit_code == '3382': return 14

            # Rule 2: Phân loại theo Section
            if section in [1, 2]:
                # Phần I & II: Ghi vào cột Staff
                if credit_code == '3383': return 8
                if credit_code == '3384': return 10
                if credit_code == '3386': return 12
                if credit_code == '3382': return 14
            elif section == 3:
                # Phần III: Ghi vào cột Company
                if credit_code == '3383': return 7
                if credit_code == '3384': return 9
                if credit_code == '3386': return 11
                if credit_code == '3382': return 13
            return None

        # Rule 4. Hàm tính tổng cột 17 (Phải trả NLĐ)
        def calc_col_17(row_data):
            # Tổng Thu Nhập (Cột 4+5+6) - Tổng Khấu Trừ NV (Cột 8+10+12+14+15+16)
            income = row_data.get(4, 0) + row_data.get(5, 0) + row_data.get(6, 0)
            deduct = row_data.get(8, 0) + row_data.get(10, 0) + row_data.get(12, 0) + row_data.get(14, 0) + row_data.get(15, 0) + row_data.get(16, 0)
            return income - deduct
        
        # section I
        grouped_values_usd = self.grouped_values(values, currency='USD')
        sheet.write(row, 0, 'I',
                    get_format(table_border_head))
        sheet.merge_range(row, 1, row, 17, 'Lương và các khoản chi phí theo lương ngoại tệ nhân viên phái cử (USD)\nSalaries and expenses for dispatched employees',
                    get_format({**table_border_head, 'align': 'left'}))
        sub_total_in_currency = {}
        sub_total = {}
        row += 1
        ordinal = 1
        sub_total_in_currency = {}
        sub_total = {}
        row += 1
        ordinal = 1
        
        for key, val in grouped_values_usd.items():
            budget_c = budget_dict.get(key[0], {}).get('code')
            debit_c = account_dict.get(key[1], '')

            # Lọc Phần I
            if budget_c not in sec_1_budgets:
                continue

            sheet.write(row, 0, ordinal, table_border_body)
            sheet.write(row, 1, budget_dict.get(key[0], {}).get('name') or '', table_border_body)
            sheet.write(row, 2, budget_c or '', table_border_body)
            sheet.write(row, 3, debit_c or '', table_border_body)
            for col in range(4, 18):
                sheet.write(row, col, '', table_border_body_number)
            row += 1

            # Dàn dữ liệu USD và VND ra các cột
            row_usd, row_vnd = {}, {}
            for credit_key, amount in val.items():
                credit_c = account_dict.get(credit_key)
                col_idx = get_col_idx(1, debit_c, credit_c) # 1 là Section I
                if col_idx:
                    row_usd[col_idx] = row_usd.get(col_idx, 0) + (amount.get('amount_currency') or 0)
                    row_vnd[col_idx] = row_vnd.get(col_idx, 0) + (amount.get('amount') or 0)

            # Rule 4: Chốt số tổng cột 17
            row_usd[17] = calc_col_17(row_usd)
            row_vnd[17] = calc_col_17(row_vnd)

            if debit_c == '3341':
                row_usd[17] = -abs(row_usd[17])
                row_vnd[17] = -abs(row_vnd[17])

            # Ghi dòng USD
            sheet.write(row, 0, '', table_border_body)
            sheet.write(row, 1, 'USD', table_border_body)
            sheet.write(row, 2, '', table_border_body)
            sheet.write(row, 3, '', table_border_body)
            for col in range(4, 18):
              amt = row_usd.get(col, '')
              sheet.write(row, col, amt, table_border_body_number)
              if amt != '': 
                  sub_total_in_currency[col] = sub_total_in_currency.get(col, 0) + amt
                  grand_total_usd[col] = grand_total_usd.get(col, 0) + amt
            row += 1

            # Ghi dòng Convert VND
            sheet.write(row, 0, '', table_border_body)
            sheet.write(row, 1, 'Convert VND', table_border_body)
            sheet.write(row, 2, '', table_border_body)
            sheet.write(row, 3, '', table_border_body)
            for col in range(4, 18):
              amt = row_vnd.get(col, '')
              sheet.write(row, col, amt, table_border_body_number)
              if amt != '': 
                  sub_total[col] = sub_total.get(col, 0) + amt
                  grand_total_vnd[col] = grand_total_vnd.get(col, 0) + amt
            
            ordinal += 1
            row += 1

        # Ghi Subtotal Phần I
        sheet.write(row, 0, '', table_border_body)
        sheet.write(row, 1, 'Subtotal _ USD', get_format({**table_border_head, 'align': 'left'}))
        sheet.write(row, 2, '', table_border_body)
        sheet.write(row, 3, '', table_border_body)
        for col in range(4, 18):
            sheet.write(row, col, sub_total_in_currency.get(col, ''), table_border_subtotal_number)
        row += 1
        
        sheet.write(row, 0, '', table_border_body)
        sheet.write(row, 1, 'Subtotal _ Convert VND', get_format({**table_border_head, 'align': 'left'}))
        sheet.write(row, 2, '', table_border_body)
        sheet.write(row, 3, '', table_border_body)
        for col in range(4, 18):
            sheet.write(row, col, sub_total.get(col, ''), table_border_subtotal_number)
        row += 1

        #============ section II =====================
        sheet.write(row, 0, 'II',
                    get_format(table_border_head))
        sheet.merge_range(row, 1, row, 17, 'Lương và các khoản chi phí theo lương ngoại tệ nhân viên nước ngoài (USD)\nSalaries and expenses for foreign employees',
                    get_format({**table_border_head, 'align': 'left'}))
        row += 1
        grouped_values_usd_2 = self.grouped_values(values, currency='USD')
        ordinal = 1
        sub_total_in_currency = {}
        sub_total = {}
        ordinal = 1
        sub_total_in_currency = {}
        sub_total = {}
        for key, val in grouped_values_usd_2.items():
            budget_c = budget_dict.get(key[0], {}).get('code')
            debit_c = account_dict.get(key[1], '')

            # Lọc Phần II
            if budget_c not in sec_2_budgets:
                continue

            sheet.write(row, 0, ordinal, table_border_body)
            sheet.write(row, 1, budget_dict.get(key[0], {}).get('name') or '', table_border_body)
            sheet.write(row, 2, budget_c or '', table_border_body)
            sheet.write(row, 3, debit_c or '', table_border_body)
            for col in range(4, 18):
                sheet.write(row, col, '', table_border_body_number)
            row += 1

            # Dàn dữ liệu USD và VND ra các cột
            row_usd, row_vnd = {}, {}
            for credit_key, amount in val.items():
                credit_c = account_dict.get(credit_key)
                col_idx = get_col_idx(2, debit_c, credit_c) # 2 là Section II
                if col_idx:
                    row_usd[col_idx] = row_usd.get(col_idx, 0) + (amount.get('amount_currency') or 0)
                    row_vnd[col_idx] = row_vnd.get(col_idx, 0) + (amount.get('amount') or 0)

            # Rule 4: Tính tổng cột 17
            row_usd[17] = calc_col_17(row_usd)
            row_vnd[17] = calc_col_17(row_vnd)

            if debit_c == '3341':
                row_usd[17] = -abs(row_usd[17])
                row_vnd[17] = -abs(row_vnd[17])

            # Ghi dòng USD
            sheet.write(row, 0, '', table_border_body)
            sheet.write(row, 1, 'USD', table_border_body)
            sheet.write(row, 2, '', table_border_body)
            sheet.write(row, 3, '', table_border_body)
            for col in range(4, 18):
              amt = row_usd.get(col, '')
              sheet.write(row, col, amt, table_border_body_number)
              if amt != '': 
                  sub_total_in_currency[col] = sub_total_in_currency.get(col, 0) + amt
                  grand_total_usd[col] = grand_total_usd.get(col, 0) + amt
            row += 1

            # Ghi dòng Convert VND
            sheet.write(row, 0, '', table_border_body)
            sheet.write(row, 1, 'Convert VND', table_border_body)
            sheet.write(row, 2, '', table_border_body)
            sheet.write(row, 3, '', table_border_body)
            for col in range(4, 18):
              amt = row_vnd.get(col, '')
              sheet.write(row, col, amt, table_border_body_number)
              if amt != '': 
                  sub_total[col] = sub_total.get(col, 0) + amt
                  grand_total_vnd[col] = grand_total_vnd.get(col, 0) + amt
            
            ordinal += 1
            row += 1

        # Ghi Subtotal Phần II
        sheet.write(row, 0, '', table_border_body)
        sheet.write(row, 1, 'Subtotal _ USD', get_format({**table_border_head, 'align': 'left'}))
        sheet.write(row, 2, '', table_border_body)
        sheet.write(row, 3, '', table_border_body)
        for col in range(4, 18):
            sheet.write(row, col, sub_total_in_currency.get(col, ''), table_border_subtotal_number)
        row += 1
        
        sheet.write(row, 0, '', table_border_body)
        sheet.write(row, 1, 'Subtotal _ Convert VND', get_format({**table_border_head, 'align': 'left'}))
        sheet.write(row, 2, '', table_border_body)
        sheet.write(row, 3, '', table_border_body)
        for col in range(4, 18):
            sheet.write(row, col, sub_total.get(col, ''), table_border_subtotal_number)
        row += 1

        #=================== section III =====================
        sheet.write(row, 0, 'III',
                    get_format(table_border_head))
        sheet.merge_range(row, 1, row, 17, 'Lương và các khoản chi phí theo lương nhân viên Việt Nam (VNĐ)\nSalaries and expenses for Vietnamese employees',
                    get_format({**table_border_head, 'align': 'left'}))
        row += 1
        
        ordinal = 1
        grouped_values_vnd = self.grouped_values(values)
        sub_total = {}
        
        # 1. Khai báo biến Dict để gom các khoản trừ (Nợ 3341)
        deduction_3341_row = {}

        for key, val in grouped_values_vnd.items():
            budget_c = budget_dict.get(key[0], {}).get('code')
            debit_c = account_dict.get(key[1], '')

            # 2. Logic bóc tách: Nếu Nợ 3341 thì gom vào deduction_3341_row và bỏ qua (không in dòng này)
            if debit_c == '3341' and budget_c in sec_3_budgets:
                for credit_key, amount in val.items():
                    credit_c = account_dict.get(credit_key)
                    col_idx = get_col_idx(3, debit_c, credit_c) # Áp dụng hàm get_col_idx để lấy đúng cột
                    if col_idx:
                        deduction_3341_row[col_idx] = deduction_3341_row.get(col_idx, 0) + (amount.get('amount') or 0)
                continue

            # 3. Lọc các dòng Section III bình thường (Phải có budget nằm trong sec_3_budgets)
            if budget_c not in sec_3_budgets:
                continue

            sheet.write(row, 0, ordinal, table_border_body)
            sheet.write(row, 1, budget_dict.get(key[0], {}).get('name') or '', table_border_body)
            sheet.write(row, 2, budget_c or '', table_border_body)
            sheet.write(row, 3, debit_c or '', table_border_body)

            row_vnd = {}
            for credit_key, amount in val.items():
                credit_c = account_dict.get(credit_key)
                col_idx = get_col_idx(3, debit_c, credit_c)
                if col_idx:
                    row_vnd[col_idx] = row_vnd.get(col_idx, 0) + (amount.get('amount') or 0)

            # Rule 4: Tính tổng cột 17 cho các dòng bình thường
            row_vnd[17] = calc_col_17(row_vnd)

            # Ghi dòng số liệu
            for col in range(4, 18):
                amt = row_vnd.get(col, '')
                sheet.write(row, col, amt, table_border_body_number)
                if amt != '': 
                    sub_total[col] = sub_total.get(col, 0) + amt
                    grand_total_vnd[col] = grand_total_vnd.get(col, 0) + amt
            
            ordinal += 1
            row += 1

        # 4. IN DÒNG GOM CHUNG DEDUCTION 3341 Ở CUỐI PHẦN III (Nếu có phát sinh)
        if deduction_3341_row:
            sheet.write(row, 0, ordinal, table_border_body)
            sheet.write(row, 1, 'Khoản trừ vào lương NV Việt Nam- Deduction on salary of Vietnamese staffs', table_border_body)
            sheet.write(row, 2, '', table_border_body) # Budget code trống
            sheet.write(row, 3, '3341', table_border_body)
            
            # Tính cột 17: Bằng -SUM của tất cả các cột phía trước
            sum_deductions = sum(deduction_3341_row.get(c, 0) for c in range(4, 17))
            deduction_3341_row[17] = -sum_deductions

            for col in range(4, 18):
                amt = deduction_3341_row.get(col, '')
                sheet.write(row, col, amt, table_border_body_number)
                if amt != '': 
                    sub_total[col] = sub_total.get(col, 0) + amt
                    grand_total_vnd[col] = grand_total_vnd.get(col, 0) + amt
            
            row += 1

        # Ghi Subtotal Phần III
        sheet.write(row, 0, '', table_border_body)
        sheet.write(row, 1, 'Subtotal _ VND', get_format({**table_border_head, 'align': 'left'}))
        sheet.write(row, 2, '', table_border_body)
        sheet.write(row, 3, '', table_border_body)
        for col in range(4, 18):
            sheet.write(row, col, sub_total.get(col, ''), table_border_subtotal_number)
        row += 1

        # 1. Ghi dòng Total USD
        sheet.write(row, 0, '', table_border_body)
        sheet.write(row, 1, 'Total USD', get_format({**table_border_head, 'align': 'left'}))
        sheet.write(row, 2, '', table_border_body)
        sheet.write(row, 3, '', table_border_body)
        for col in range(4, 18):
            val = grand_total_usd.get(col, 0)
            # Quy tắc: Nếu bằng 0 thì để trống (''), ngược lại ghi giá trị
            sheet.write(row, col, val if val != 0 else '', table_border_subtotal_number)
        row += 1

        # 2. Ghi dòng Total VND
        sheet.write(row, 0, '', table_border_body)
        sheet.write(row, 1, 'Total VND', get_format({**table_border_head, 'align': 'left'}))
        sheet.write(row, 2, '', table_border_body)
        sheet.write(row, 3, '', table_border_body)
        for col in range(4, 18):
            val = grand_total_vnd.get(col, 0)
            # Quy tắc: Nếu bằng 0 thì để trống (''), ngược lại ghi giá trị
            sheet.write(row, col, val if val != 0 else '', table_border_subtotal_number)
        row += 1

        # ==============================================================================
        # PHẦN BỔ SUNG: THÔNG TIN NGÀY LẬP VÀ CHỮ KÝ PHÍA DƯỚI CÙNG
        # ==============================================================================
        row += 1  # Cách ra 1 dòng trống cho thoáng bảng dữ liệu
        
        # Tự động lấy ngày chạy báo cáo hiện tại để hiển thị đúng format template
        from datetime import datetime
        today = datetime.today()
        date_text = f"Prepared, Date on {today.day:02d} month {today.month:02d} year {today.year}"
        sheet.write(row, 0, date_text, get_format({'font_name': 'Times New Roman', 'font_size': 11, 'italic': True}))
        
        row += 2  # Tạo khoảng cách chiều cao trống vừa đủ để ký tên
        
        # Định dạng chuẩn cho phần chức danh ký tên (Chữ đậm, căn giữa cột, cho phép xuống dòng)
        sign_format = get_format({'font_name': 'Times New Roman', 'font_size': 12, 'bold': True, 'align': 'center', 'text_wrap': True})
        
        # Phân bổ vị trí người ký đều ra các cột theo trục ngang của báo cáo
        sheet.write(row, 1, "Người lập biểu\n(Prepared by)", sign_format)
        sheet.write(row, 8, "Kế toán trưởng\n(Chief Accountant)", sign_format)
        sheet.write(row, 15, "Phê duyệt bởi\n(Approved by)", sign_format)
        
        row += 1

    def grouped_values(self, values, currency='VND'):
        grouped_vals = {}
        for val in values:
            if val.get('currency_name') == currency:
                key = (val.get('budget_code_id'), val.get('debit_account_id'))
                credit_acc = val.get('credit_account_id')
                
                if key not in grouped_vals:
                    # Dùng val.copy() để tạo một bản sao, tránh làm biến đổi data gốc từ SQL
                    grouped_vals[key] = {
                        credit_acc: val.copy()
                    }
                else:
                    if credit_acc in grouped_vals[key]:
                        # CỘNG DỒN CẢ 2 TRƯỜNG VND VÀ USD
                        grouped_vals[key][credit_acc]['amount'] += (val.get('amount') or 0)
                        grouped_vals[key][credit_acc]['amount_currency'] += (val.get('amount_currency') or 0)
                    else:
                        grouped_vals[key][credit_acc] = val.copy()
        return grouped_vals

    def get_lines(self, o):
        query = """
            SELECT
                row_number() over() as id,
                oos.category_id,
                oos_category.parent_id AS parent_category_id,
                oos.item_code,
                oos.item_name,
                oos.budget_code_id,
                oos.description AS oos_description,
                COALESCE(ABS(SUM(aal.amount)), 0) as amount,
                COALESCE(ABS(SUM(aml.amount_currency)), 0) as amount_currency,
                oos.credit_account_id,
                oos.debit_account_id,
                rc.name AS currency_name,
                oos.company_id
            FROM oos_mapping oos
                LEFT JOIN account_analytic_line aal ON aal.oos_mapping_id = oos.id
                LEFT JOIN oos_mapping_category oos_category ON oos_category.id = oos.category_id
                LEFT JOIN account_move_line aml ON aml.id = aal.move_line_id
                LEFT JOIN res_currency rc ON rc.id = aml.currency_id
            WHERE aml.date >= {date_from} AND aml.date <= {date_to}
            GROUP BY oos.category_id,
                oos_category.parent_id,
                oos.item_code,
                oos.item_name,
                oos.budget_code_id,
                oos.description,
                oos.credit_account_id,
                oos.debit_account_id,
                rc.name,
                oos.company_id
""" .format(
            date_from="'%s'" % o.from_date.strftime(
                DEFAULT_SERVER_DATE_FORMAT),
            date_to="'%s'" % o.to_date.strftime(
                DEFAULT_SERVER_DATE_FORMAT),
        )
        self.env.cr.execute(query)
        vals = self.env.cr.dictfetchall()
        return vals
