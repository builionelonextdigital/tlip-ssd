# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.safe_eval import safe_eval

cols = {
    # TODO: Change einvoice_form_no, einvoice_no to field einvoice_line_ids (model e.invoice.line)
    'move_id.minvoice_template_id.invoice_series': 0,
    'move_id.minvoice_no': 1,
    'move_id.invoice_date': 2,
    'move_id.partner_id.name': 3,
    'move_id.partner_id.vat': 4,
    'product_id.name': 5,
    'price_subtotal': 6,
    'tax_id': 7,
    'tax_amount': 8,
    'move_id.name': 9
}


class report_invoice_list_xlsx(models.AbstractModel):
    _name = 'report.biz_sales_invoice_list.report_invoice_list_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report_invoice_list_xlsx'

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
        table_border_body = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'border': True, 'align': 'left', 'num_format': '#,###',
                                                'right': 1, 'text_wrap': True
                                                 })
        table_border_body_category_bold = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'left',
                                                               'num_format': '#,##0.00', 'bold': True, 'right': 1})
        table_border_body_category_bold.set_bottom(4)
        table_border_body_number = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 12, 'shrink': True, 'align': 'right',  'num_format': '#,###',
                                                        'right': 1})
        table_border_body_number.set_bottom(4)

        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman',
                            'font_size': 12, 'valign': 'vcenter', 'align': 'left'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)

        sheet = workbook.add_worksheet("BKĐR")
        # sheet.hide_gridlines(2)
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 15)

        company_id = self.env.company
        y_offset = 0
        company_id = self.env.company
        sheet.write(y_offset, 0, '%s' % (
                    company_id.name), get_format({'bold': True}))
        y_offset += 1
        sheet.write(y_offset, 0, 'Địa chỉ: %s' % (
            self.get_company_address(company_id)), get_format({'bold': True}))
        y_offset += 2
        sheet.merge_range(y_offset, 0, y_offset, 10, 'BẢNG KÊ HÓA ĐƠN, CHỨNG TỪ HÀNG HÓA, DỊCH VỤ BÁN RA', get_format(
            {'font_size': 16, 'bold': True, 'align': 'center'}))
        y_offset += 1
        sheet.merge_range(y_offset, 0, y_offset, 10, 'Từ ngày: %s   Đến ngày: %s' % (o.from_date, o.to_date), get_format(
            {'font_size': 12, 'bold': True, 'align': 'center'}))
        y_offset += 2
        # header table
        sheet.write(y_offset, 0, 'KÝ HIỆU HĐ',
                    get_format(table_border_head))
        sheet.write(y_offset, 1, 'SỐ HĐ',
                    get_format(table_border_head))
        sheet.write(y_offset, 2, 'NGÀY',
                    get_format(table_border_head))
        sheet.write(y_offset, 3, 'TÊN Đ.V - K.HÀNG',
                    get_format(table_border_head))
        sheet.write(y_offset, 4, 'MÃ SỐ THUẾ',
                    get_format(table_border_head))
        sheet.write(y_offset, 5, 'TÊN HÀNG',
                    get_format(table_border_head))
        sheet.write(y_offset, 6, 'DOANH SỐ',
                    get_format(table_border_head))
        sheet.write(y_offset, 7, 'THUẾ SUẤT',
                    get_format(table_border_head))
        sheet.write(y_offset, 8, 'THUẾ GTGT',
                    get_format(table_border_head))
        sheet.write(y_offset, 9, 'CHỨNG TỪ',
                    get_format(table_border_head))
        y_offset += 1

        lines = self.get_lines(o)
        row = y_offset
        total_amount = 0
        total_tax_amount = 0
        for line in lines:
            for col in cols:
                tax_list = line.tax_ids.mapped('amount')
                if col == 'tax_id':
                    tax_str = ', '.join(str(int(tax)) for tax in tax_list)
                    sheet.write(row, cols[col], tax_str,
                                table_border_body)
                elif col == 'tax_amount':
                    tax_amount = 0
                    for tax in tax_list:
                        tax_amount += tax * line.price_subtotal / 100
                    sheet.write(row, cols[col], tax_amount,
                                table_border_body)
                    total_tax_amount += tax_amount
                else:
                    write_val = safe_eval('line.%s' %
                                          col, {'line': line}, mode='eval')
                    if col == 'move_id.minvoice_no':
                        write_val = write_val and str(write_val).zfill(8) or ''
                    if col == 'product_id.name':
                        write_val = line.product_id.name or line.name
                    if col == 'price_subtotal':
                        total_amount += write_val
                    if col in ['move_id.invoice_date']:
                        if write_val:
                            write_val = write_val.strftime(
                                DEFAULT_SERVER_DATE_FORMAT)
                    sheet.write(row, cols[col], write_val,
                                table_border_body)
            row += 1

        sheet.merge_range(row, 0, row, 5, 'Tổng cộng',
                          get_format(table_border_head))
        sheet.write(row, 6, total_amount, table_border_body)
        sheet.write(row, 7, '', get_format(table_border_head))
        sheet.write(row, 8, total_tax_amount, table_border_body)
        sheet.write(row, 9, '', get_format(table_border_head))

        row += 2
        sheet.merge_range(row, 1, row, 3, 'Người lập biểu',
                          get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(row, 6, row, 8, 'Kế toán trưởng',
                          get_format({'bold': True, 'align': 'center'}))
        row += 1
        sheet.merge_range(row, 1, row, 3, '(Ký, họ tên)', get_format({'align': 'center'}))
        sheet.merge_range(row, 6, row, 8, '(Ký, họ tên)', get_format({'align': 'center'}))

    def get_lines(self, o):
        domain = [
            ('state', '=', 'posted'),
            ('date', '>=', o.from_date),
            ('date', '<=', o.to_date),
            ('company_id', '=', self.env.company.id),
            ('journal_id.type', '=', 'sale')
        ]
        account_move = self.env['account.move'].search(
            domain, order="date asc")
        return account_move.invoice_line_ids

    def check_tax(self, tax_ids, name_vat):
        if name_vat:
            if tax_ids.filtered(lambda x: x.name == name_vat):
                return True
            return False

        return True
