# -*- coding: utf-8 -*-
from odoo import api, models, fields
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
# from openpyxl.styles.borders import Borders, Side
from openpyxl.styles.borders import Border, Side


class ReportCashFlowsXlsx(models.AbstractModel):
    _name = 'report.biz_cash_flows_report.rp_cash_flows'
    _inherit = 'report.report_xlsx.abstract'
    _description = "Statements Cash Flows"

    def generate_xlsx_report(self, workbook, data, details):
        self = self.with_context(lang=self.env.user.lang)
        image_content = {'font_name': 'Times New Roman', 'font_size': 22, 'bold': True, 'align': 'center',
                         'valign': 'vcenter'}
        table_border_head = {
            'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True,
            'align': 'center', 'border': True, 'bold': True, 'right': 5,'left': 5,'top': 5,'bottom': 5
        }
        table_border_body = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'center',
                             'border': True, 'num_format': '#,##0.00'}
        table_border_body_last = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'center',
                             'top': 5, 'num_format': '#,##0.00'}

        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman', 'font_size': 12, 'valign': 'vcenter', 'align': 'left'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)

        for o in details:
            sheet = workbook.add_worksheet("BÁO CÁO LƯU CHUYỂN TIỀN TỆ")
            sheet.hide_gridlines(2)
            sheet.set_column(0, 0, 60)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 15)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 15)

            company_id = self.env.company
            y_offset = 0
            sheet.write(y_offset, 0, 'Đơn vị báo cáo: %s' %(company_id.name), get_format({'bold': True}))
            # sheet.border = Border(top=Side(style='thick'))
            sheet.merge_range(y_offset, 2, y_offset, 4, 'Mẫu số B03 - DN', get_format({'align': 'center', 'bold': True}))
            y_offset += 1
            sheet.write(y_offset, 0, self.get_company_address(company_id), get_format({'bold': True, 'text_wrap': True}))
            sheet.merge_range(y_offset, 2, y_offset + 1, 4,
                              "(Ban hành theo thông tư số 200/2014/TT-BTC\nNgày 22/12/2014 của bộ tài chính)",
                              get_format({'align': 'center', 'text_wrap': True, 'italic': True}))
            y_offset += 3
            sheet.merge_range(y_offset, 0, y_offset, 4, 'BÁO CÁO LƯU CHUYỂN TIỀN TỆ',
                              get_format({'font_size': 12, 'bold': True, 'align': 'center'}))
            y_offset += 1
            sheet.merge_range(y_offset, 0, y_offset, 4, '(Theo phương pháp trực tiếp)(*)', get_format({'align': 'center', 'italic': True, 'bold': True,}))
            y_offset += 1
            sheet.merge_range(y_offset, 0, y_offset, 4, 'Năm %s' % (o.from_date.strftime('%Y')), get_format({'align': 'center'}))
            y_offset += 2
            sheet.merge_range(y_offset, 0, y_offset, 4, 'Đơn vị tính: %s' %(company_id.currency_id.name), get_format({'align': 'right'}))
            y_offset += 1
            sheet.write(y_offset, 0, 'Chỉ tiêu', get_format(table_border_head))
            sheet.write(y_offset, 1, 'Mã số', get_format(table_border_head))
            sheet.write(y_offset, 2, 'Thuyết minh', get_format(table_border_head))
            sheet.write(y_offset, 3, 'Năm nay', get_format(table_border_head))
            sheet.write(y_offset, 4, 'Năm trước', get_format(table_border_head))
            y_offset += 1
            sheet.write(y_offset, 0, '1', get_format({'border': True, 'align': 'center'}))
            sheet.write(y_offset, 1, '2', get_format({'border': True, 'align': 'center'}))
            sheet.write(y_offset, 2, '3', get_format({'border': True, 'align': 'center'}))
            sheet.write(y_offset, 3, '4', get_format({'border': True, 'align': 'center'}))
            sheet.write(y_offset, 4, '5', get_format({'right': 5, 'align': 'center'}))
            y_offset += 1
            for line in o.line_ids.sorted('stt_calculate'):
                table_border_body_category_config = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'left',
                             'border': True, 'num_format': '#,##0.00'}
                table_border_body_number = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True,
                                            'align': 'right',
                                            'border': True, 'num_format': '#0'}
                table_border_body_number_right = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True,
                                                  'align': 'right',
                                                  'border': True, 'num_format': '#0', 'right': 5}
                table_border_body_tr = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'center',
                                     'border': True, 'num_format': '#,##0.00'}
                table_border_body_code = {'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'center',
                                          'border': True, 'num_format': '#,##'}
                if line.balance_id.is_bold_report:
                    table_border_body_category_config.update({'bold': True})
                    table_border_body_tr.update({'bold': True})
                    table_border_body_number.update({'bold': True})
                    table_border_body_number_right.update({'bold': True})
                    table_border_body_code.update({'bold': True})
                if line.balance_id.is_italic_report:
                    table_border_body_category_config.update({'italic': True})
                    table_border_body_tr.update({'italic': True})
                    table_border_body_number.update({'italic': True})
                    table_border_body_number_right.update({'italic': True})
                    table_border_body_code.update({'italic': True})

                sheet.write(y_offset, 0, line.balance_id.categ_name or '', get_format(table_border_body_category_config))
                sheet.write(y_offset, 1, line.code or '', get_format(table_border_body_code))
                sheet.write(y_offset, 2, '', get_format(table_border_body_tr))
                sheet.write(y_offset, 3, self.format_float_number(line, line.number_first_year), get_format(table_border_body_number))
                sheet.write(y_offset, 4, self.format_float_number(line, line.number_last_year), get_format(table_border_body_number_right))
                y_offset += 1
            sheet.write(y_offset, 0, '', get_format(table_border_body_last))
            sheet.write(y_offset, 1, '', get_format(table_border_body_last))
            sheet.write(y_offset, 2, '', get_format(table_border_body_last))
            sheet.write(y_offset, 3, '', get_format(table_border_body_last))
            sheet.write(y_offset, 4, '', get_format(table_border_body_last))

            y_offset += 1
            sheet.write(y_offset, 0, 'Ghi chú: Các chỉ tiêu không có số liệu thì doanh nghiệp không phải trình bày nhưng không được đánh lại “Mã số” chỉ tiêu', get_format({'align': 'left'}))

            y_offset += 2
            sheet.merge_range(y_offset, 2, y_offset, 4,
                              'Lập, %s' % (datetime.now().strftime('ngày %d tháng %m năm %Y')),
                              get_format({'bold': True, 'italic': True, 'align': 'right'}))
            y_offset += 1
            sheet.write(y_offset, 0, 'Người lập biểu', get_format({'bold': True, 'align': 'center'}))
            sheet.merge_range(y_offset, 1, y_offset, 2, 'Kế toán trưởng', get_format({'bold': True, 'align': 'center'}))
            sheet.merge_range(y_offset, 3, y_offset, 4, 'Giám đốc', get_format({'bold': True, 'align': 'center'}))
            y_offset += 1
            sheet.write(y_offset, 0, '(Ký, họ tên)', get_format({'align': 'center'}))
            sheet.merge_range(y_offset, 1, y_offset, 2, '(Ký, họ tên)', get_format({'align': 'center'}))
            sheet.merge_range(y_offset, 3, y_offset, 4, '(Ký, họ tên, đóng dấu)', get_format({'align': 'center'}))

            y_offset += 1
            sheet.write(y_offset, 0, '- Số chứng chỉ hành nghề;', get_format({'align': 'center'}))
            y_offset += 1
            sheet.write(y_offset, 0, '- Đơn vị cung cấp dịch vụ kế toán', get_format({'align': 'center'}))

            y_offset += 5
            sheet.merge_range(y_offset, 0, y_offset + 1, 4, 'Đối với người lập biểu là các đơn vị dịch vụ kế toán phải ghi rõ Số chứng chỉ hành nghề, tên và địa chỉ Đơn vị cung cấp dịch vụ kế toán. Người lập biểu là cá nhân ghi rõ Số chứng chỉ hành nghề.', get_format({'italic': True, 'align': 'left', 'text_wrap': True}))



    def get_company_address(self, company):
        address = 'Địa chỉ: '
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