# -*- coding: utf-8 -*-
from odoo import api, models, fields
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class ReportAccountingBalanceXlsx(models.AbstractModel):
    _name = 'report.biz_accounting_balance_sheet.rp_account_balance_sheet'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Accounting Balance Sheet"
    
    def generate_xlsx_report(self, workbook, data, details):
        self = self.with_context(lang=self.env.user.lang)
        image_content = {'font_name': 'Times New Roman', 'font_size': 22, 'bold': True, 'align': 'center', 'valign':'vcenter'}
        table_border_head = {
            'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True, 
            'align': 'center','border':True,'bold':True,
        }
        table_border_body = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'left', 'num_format': '#,###',
                                                 'right': 1
                             })
        table_border_body.set_bottom(4)
        table_border_body_first = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'center','border':True, 'num_format': '#,###'}
        table_border_body_category_bold = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'left',
                             'num_format': '#,##0.00', 'bold': True, 'right': 1})
        table_border_body_category_bold.set_bottom(4)
        table_border_body_number = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'right',  'num_format': '#,###',
                                                        'right': 1})
        table_border_body_number.set_bottom(4)
        table_border_body_last = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'center',
                             'top': 1, 'num_format': '#,##0.00'})

        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman', 'font_size': 12,'valign':'vcenter','align': 'left'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)

        for o in details:
            sheet = workbook.add_worksheet("BẢNG CÂN ĐỐI KẾ TOÁN")
            sheet.hide_gridlines(2)
            sheet.set_column(0,0,60)
            sheet.set_column(1,1,15)
            sheet.set_column(2,2,15)
            sheet.set_column(3,3,15)
            sheet.set_column(4,4,15)

            company_id = self.env.company
            y_offset=0
            sheet.write(y_offset, 0, 'Đơn vị báo cáo: %s' %(company_id.name), get_format({'bold': True}))
            sheet.merge_range(y_offset, 2, y_offset, 4,  'Mẫu số B 01 - DN', get_format({'align': 'center', 'bold': True}))
            y_offset+=1
            sheet.write(y_offset, 0, 'Địa chỉ: ' + self.get_company_address(company_id), get_format({'bold': True, 'text_wrap': True}))
            sheet.merge_range(y_offset, 2, y_offset+1, 4, "(Ban hành theo thông tư số 200/2014/YY-BTC\nNgày 22/12/2014 của bộ tài chính)", get_format({'align': 'center', 'text_wrap': True, 'italic': True}))
            y_offset+=3
            sheet.merge_range(y_offset, 0, y_offset, 4, 'BẢNG CÂN ĐỐI KẾ TOÁN' , get_format({'font_size': 16,'bold': True, 'align': 'center'}))
            y_offset+=1
            sheet.merge_range(y_offset, 0, y_offset, 4, 'Tại ngày %s tháng %s năm %s (1)' % (o.to_date.strftime('%d'), o.to_date.strftime('%m'), o.to_date.strftime('%Y')), get_format({'align': 'center'}))
            y_offset+=1
            sheet.merge_range(y_offset, 0, y_offset, 4, '(Áp dụng cho doanh nghiệp đáp ứng giả định hoạt động liên tục)', get_format({'align': 'center', 'italic': True}))

            y_offset+=2
            sheet.merge_range(y_offset, 0, y_offset, 4, 'Đơn vị tính: %s' %(company_id.currency_id.name), get_format({'align': 'right'}))
            y_offset+=1
            sheet.write(y_offset, 0, 'TÀI SẢN', get_format(table_border_head))
            sheet.write(y_offset, 1, 'Mã số', get_format(table_border_head))
            sheet.write(y_offset, 2, 'Thuyết minh', get_format(table_border_head))
            sheet.write(y_offset, 3, 'Số cuối năm (3)', get_format(table_border_head))
            sheet.write(y_offset, 4, 'Số đầu năm (4)', get_format(table_border_head))
            y_offset+=1
            sheet.write(y_offset, 0, '1', get_format(table_border_body_first))
            sheet.write(y_offset, 1, '2', get_format(table_border_body_first))
            sheet.write(y_offset, 2, '3', get_format(table_border_body_first))
            sheet.write(y_offset, 3, '4', get_format(table_border_body_first))
            sheet.write(y_offset, 4, '5', get_format(table_border_body_first))
            y_offset+=1
            for line in o.line_ids.sorted('code'):
                table_border_body = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'left',
                                     'num_format': '#,###', 'right': 1}
                table_border_body_code = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'center',
                                     'num_format': '#,###', 'right': 1}
                table_border_body_number = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True,
                                            'align': 'right', 'num_format': '#,###', 'right': 1}
                if line.balance_id.is_bold_report:
                    table_border_body.update({'bold': True})
                    table_border_body_code.update({'bold': True})
                    table_border_body_number.update({'bold': True})
                table_border_body_final = workbook.add_format(table_border_body)
                table_border_body_code = workbook.add_format(table_border_body_code)
                table_border_body_number_final = workbook.add_format(table_border_body_number)
                table_border_body_final.set_bottom(4)
                table_border_body_number_final.set_bottom(4)
                table_border_body_code.set_bottom(4)
                sheet.write(y_offset, 0, line.balance_id.display_name or '', (table_border_body_final))
                sheet.write(y_offset, 1, line.code, (table_border_body_code))
                sheet.write(y_offset, 2, '', (table_border_body_final))
                sheet.write(y_offset, 3, self.format_float_number(line, line.number_last_year), (table_border_body_number_final))
                sheet.write(y_offset, 4, self.format_float_number(line, line.number_first_year), (table_border_body_number_final))
                y_offset += 1
            sheet.write(y_offset, 0, '', (table_border_body_last))
            sheet.write(y_offset, 1, '', (table_border_body_last))
            sheet.write(y_offset, 2, '', (table_border_body_last))
            sheet.write(y_offset, 3, '', (table_border_body_last))
            sheet.write(y_offset, 4, '', (table_border_body_last))

            y_offset+=1
            sheet.merge_range(y_offset, 3, y_offset, 4, 'Lập, %s' % (datetime.now().strftime('ngày %d tháng %m năm %Y')), get_format({'bold': True, 'italic': True, 'align': 'right'}))
            y_offset+=2
            sheet.write(y_offset, 0, 'Người lập biểu', get_format({'bold': True, 'align': 'center'}))
            sheet.merge_range(y_offset, 1, y_offset, 2, 'Kế toán trưởng', get_format({'bold': True, 'align': 'center'}))
            sheet.merge_range(y_offset, 3, y_offset, 4, 'Giám đốc', get_format({'bold': True, 'align': 'center'}))
            y_offset+=1
            sheet.write(y_offset, 0, '(Ký, họ tên)', get_format({'align': 'center'}))
            sheet.merge_range(y_offset, 1, y_offset, 2, '(Ký, họ tên)', get_format({'align': 'center'}))
            sheet.merge_range(y_offset, 3, y_offset, 4, '(Ký, họ tên, đóng dấu)', get_format({'align': 'center'}))

            y_offset += 1
            sheet.write(y_offset, 0, '- Số chứng chỉ hành nghề;', get_format({'align': 'center'}))
            y_offset += 1
            sheet.write(y_offset, 0, '- Đơn vị cung cấp dịch vụ kế toán', get_format({'align': 'center'}))

            y_offset += 5
            sheet.merge_range(y_offset, 0, y_offset, 4, 'Ghi chú:', get_format({'italic': True, 'align': 'left', 'text_wrap': True}))
            y_offset += 1
            sheet.merge_range(y_offset, 0, y_offset, 4, '(1) Những chỉ tiêu không có số liệu được miễn trình bày nhưng không được đánh lại “Mã số” chỉ tiêu.', get_format({'italic': True, 'align': 'left', 'text_wrap': True}))
            y_offset += 1
            sheet.merge_range(y_offset, 0, y_offset, 4, '(2) Số liệu trong các chỉ tiêu có dấu (*) được ghi bằng số âm dưới hình thức ghi trong ngoặc đơn (...).', get_format({'italic': True, 'align': 'left', 'text_wrap': True}))
            y_offset += 1
            sheet.merge_range(y_offset, 0, y_offset, 4, '(3) Đối với doanh nghiệp có kỳ kế toán năm là năm dương lịch (X) thì “Số cuối năm“ có thể ghi là “31.12.X“; “Số đầu năm“ có thể ghi là “01.01.X“.', get_format({'italic': True, 'align': 'left', 'text_wrap': True}))
            y_offset += 1
            sheet.merge_range(y_offset, 0, y_offset + 1, 4, '(4) Đối với người lập biểu là các đơn vị dịch vụ kế toán phải ghi rõ Số chứng chỉ hành nghề,  tên và địa chỉ Đơn vị cung cấp dịch vụ kế toán. Người lập biểu là cá nhân ghi rõ Số chứng chỉ hành nghề.', get_format({'italic': True, 'align': 'left', 'text_wrap': True}))

    def get_company_address(self, company):
        address = ''
        if company:
            if company.street:
                address += company.street
            if company.street2:
                address += len(address) > 0 and ', ' + company.street2 or company.street2
            if company.city:
                address += len(address) > 0 and ', ' + company.city or company.city
            if company.state_id:
                address += len(address) > 0 and ', ' + company.state_id.name or company.state_id.name
            if company.country_id:
                address += len(address) > 0 and ', ' + company.country_id.name or company.country_id.name
        return address

    def format_float_number(self, line, number):
        if not line.code and not line.apply_by:
            number_format = None
        else:
            if number >= 0:
                if number % 1 == 0:
                    number_format = "{:,.0f}".format(number)
                else:
                    number_format = "{:,.2f}".format(number)
            else:
                number = abs(number)
                if number % 1 == 0:
                    number_format = "(" + "{:,.0f}".format(number) + ")"
                else:
                    number_format = "(" + "{:,.2f}".format(number) + ")"

        return number_format