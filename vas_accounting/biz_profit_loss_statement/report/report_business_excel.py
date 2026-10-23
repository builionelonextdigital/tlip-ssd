# -*- coding: utf-8 -*-
from odoo import models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import base64
import io
from urllib.request import Request, urlopen

cols = {
    'chi_tieu':0,
    'ma_so':1,
    'thuyet_minh':2,
    'nam_nay':3,
    'nam_truoc':4,
}


class RevenueReportXlsx(models.AbstractModel):
    _name = 'report.biz_profit_loss_statement.report_business_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, details):
        for o in details:
            sheet = workbook.add_worksheet(_('Business Activities Results'))
            company_name_style = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 16, 'valign':'vcenter', 'bold': True, 'text_wrap': True})
            title_style = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'valign':'vcenter', 'font_size': 16,'bold': True})
            description_style = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'valign':'vcenter', 'font_size': 16})
            description_style_l = workbook.add_format({'font_name': 'Times New Roman','align': 'left', 'valign':'vcenter', 'font_size': 16})
            description_style_l_italic = workbook.add_format({'font_name': 'Times New Roman','text_wrap': True,'italic': True, 'align': 'left', 'valign':'vcenter', 'font_size': 16})
            name_form_style = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'valign':'vcenter', 'font_size': 18, 'bold': True})
            time_style = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'valign':'vcenter', 'font_size': 18})
            time_style.set_italic()
            title_table_style = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'font_size': 16, 'valign':'vcenter', 'border': 1, 'bold': True})
            chitieu_table_style = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 16, 'valign':'vcenter', 'left': 1,
                    'right': 1
                })
            table_style = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'font_size': 16, 'valign':'vcenter', 'left': 1,
                    'right': 1
                })

            table_style_r = workbook.add_format({'font_name': 'Times New Roman', 'align': 'right', 'font_size': 16, 'valign':'vcenter', 'left': 1,
                    'right': 1
                })
            ghichu_style = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 16, 'valign':'vcenter', 'top': 1})
            information_style = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'font_size': 16, 'valign':'vcenter','bold': True})
            signature_style = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 16, 'valign':'vcenter','align': 'center',})

            sheet.set_margins(0.25,0.25,0.25,0.75)
            sheet.set_column(0,0,97)
            sheet.set_column(1,1,15)
            sheet.set_column(2,2,15)
            sheet.set_column(3,3,24)
            sheet.set_column(4,4,24)
            sheet.hide_gridlines(2)
            company = self.env.company

            sheet.write('A1','Đơn vị báo cáo: ' + company.name or '', company_name_style)
            sheet.merge_range('B1:E1', 'Mẫu số B 02 - DN', title_style)

            sheet.merge_range('A2:A3', 'Địa chỉ: %s' % self.get_company_address(company), company_name_style)
            sheet.merge_range('B2:E2', '(Ban hành theo Thông tư số 200/2014/TT-BTC', description_style)

            sheet.merge_range('B3:E3', 'Ngày 22/12/2014 của Bộ Tài chính)', description_style)

            sheet.merge_range('A6:E6', 'BÁO CÁO KẾT QUẢ HOẠT ĐỘNG SẢN XUẤT KINH DOANH (Mẫu số B 02 - DN )', name_form_style)

            sheet.merge_range('A7:E7', 'Năm %s' %(o.date_from.strftime('%Y')), time_style)

            sheet.merge_range('C8:D8', 'Đơn vị tính:%s' %('..........' if not self.env.company.currency_id.name else self.env.company.currency_id.name), time_style)

            sheet.write('A9', 'CHỈ TIÊU', title_table_style)
            sheet.write('B9', 'Mã số', title_table_style)
            sheet.write('C9', 'Thuyết minh', title_table_style)
            sheet.write('D9', 'Năm nay', title_table_style)
            sheet.write('E9', 'Năm trước', title_table_style)

            sheet.write('A10', '1', title_table_style)
            sheet.write('B10', '2', title_table_style)
            sheet.write('C10', '3', title_table_style)
            sheet.write('D10', '4', title_table_style)
            sheet.write('E10', '5', title_table_style)

            for i in range(0, 9):
                sheet.set_row(i, 30)

            y_offset= 10
            sheet.set_row(y_offset, 30)
            lines = self.get_lines(o)
            for line in lines:
                for key,val in line.items():
                    if key == 'chi_tieu':
                        sheet.write(y_offset, cols[key], val or '', chitieu_table_style)
                    elif key in ['nam_nay','nam_truoc']:
                        sheet.write(y_offset, cols[key], val or '', table_style_r)
                    else:
                        sheet.write(y_offset, cols[key], val or '', table_style)
                y_offset += 1
                sheet.set_row(y_offset, 30)

            date_now = datetime.today()

            sheet.write(y_offset,0, '(*)Chỉ áp dụng tại công ty cổ phần', ghichu_style)
            sheet.write(y_offset,1, '', ghichu_style)
            sheet.write(y_offset,2, '', ghichu_style)
            sheet.write(y_offset,3, '', ghichu_style)
            sheet.write(y_offset,4, '', ghichu_style)
            
            y_offset += 1
            sheet.merge_range(y_offset,2,y_offset,4, 'Lập ngày %s tháng %s năm %s' %(date_now.day, date_now.month,date_now.year), information_style)
            
            y_offset += 1
            sheet.write(y_offset,0, 'Người lập biểu', information_style)
            sheet.merge_range(y_offset,1,y_offset,2, 'Kế toán trưởng', information_style)
            sheet.merge_range(y_offset,3,y_offset,4, 'Giám đốc', information_style)

            y_offset += 1
            sheet.write(y_offset,0, '(Ký, họ tên)', signature_style)
            sheet.merge_range(y_offset,1,y_offset,2, '(Ký, họ tên)', signature_style)
            sheet.merge_range(y_offset,3,y_offset,4, '(Ký, họ tên, đóng dấu)', signature_style)
            y_offset += 5
            sheet.merge_range(y_offset,0,y_offset,4, '- Số chứng chỉ hành nghề;', description_style_l)
            y_offset +=1
            sheet.merge_range(y_offset,0,y_offset,4, '- Đơn vị cung cấp dịch vụ kế toán;', description_style_l)
            y_offset +=1
            sheet.set_row(y_offset,40)
            sheet.merge_range(y_offset,0,y_offset,4, 'Đối với người lập biểu là các đơn vị dịch vụ kế toán phải ghi rõ Số chứng chỉ hành nghề, tên và địa chỉ Đơn vị cung cấp dịch vụ kế toán. Người lập biểu là cá nhân ghi rõ Số chứng chỉ hành nghề', description_style_l_italic)

    def get_lines(self,o):
        res=[]
        no = 0
        for line in o.business_activities_results_line_ids:
            val = {
                    'chi_tieu':line.target_config_id.targets_name,
                    'ma_so':line.code or '',
                    'thuyet_minh':line.present or '',
                    'nam_nay':self.format_float_number(line.this_year),
                    'nam_truoc':self.format_float_number(line.year_ago),
                }

            res.append(val)

        return res

    def format_float_number(self, num):
        if not num:
            return '0'

        number = float(num)
        if number % 1 == 0:
            return "{:,.0f}".format(number)
        else:
            return "{:,.2f}".format(number).rstrip('0')

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