# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, date

cols = {
    'stt': 0,
    'move_id.name': 1,
    # TODO: Change einvoice_form_no, einvoice_serial, einvoice_no to field einvoice_line_ids (model e.invoice.line)
    'move_id.einvoice_form_no': 2,
    'move_id.einvoice_serial': 3,
    'move_id.einvoice_no': 4,
    'move_id.invoice_date': 5,
    'move_id.partner_id.name': 6,
    'move_id.partner_id.vat': 7,
    'product_id.name': 8,
    'product_uom_id.name': 9,
    'quantity': 10,
    'price_unit': 11,
    'price_subtotal': 12,
    'tax_id': 13,
    'tax_amount': 14,
    'note': 15,
}


class PurchaseReceipSheetXlsx(models.AbstractModel):
    _name = 'report.biz_purchase_invoices_list.purchase_receipt_sheet_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, details):
        for o in details:
            self = self.with_context(lang=self.env.user.lang)

            table_border_head = {
                'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True,
                'align': 'center', 'border': True, 'bold': True, 'bg_color': '#D3D3D3'
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

            for o in details:
                sheet = workbook.add_worksheet("BKMV")
                # sheet.hide_gridlines(2)
                sheet.set_column(0, 0, 5)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 2, 15)
                sheet.set_column(3, 3, 15)
                sheet.set_column(4, 4, 15)
                sheet.set_column(5, 5, 50)
                sheet.set_column(6, 6, 20)
                sheet.set_column(7, 7, 40)
                sheet.set_column(8, 8, 15)
                sheet.set_column(9, 9, 15)
                sheet.set_column(10, 10, 15)
                sheet.set_column(12, 12, 15)

                company_id = self.env.company
                y_offset = 0
                sheet.merge_range(y_offset, 0, y_offset, 10, 'BẢNG KÊ HÓA ĐƠN, CHỨNG TỪ HÀNG HÓA, DỊCH VỤ MUA VÀO', get_format(
                    {'font_size': 16, 'bold': True, 'align': 'center'}))
                sheet.merge_range(y_offset, 11, y_offset, 14,  'Mẫu số: 01-1/HT',
                                  get_format({'align': 'center', 'bold': True}))
                y_offset += 1
                sheet.merge_range(y_offset, 11, y_offset+1, 14, "((Ban hành kèm theo Thông tư số\n80/2021/TT-BTC ngày 29 tháng 9 năm 2021 của Bộ\nrưởng Bộ Tài chính)",
                                  get_format({'align': 'center', 'text_wrap': True, 'italic': True}))
                y_offset += 2
                sheet.write(y_offset, 0, '[02] Tên người nộp thuế: %s' % (
                    company_id.name), get_format({'bold': True}))
                y_offset += 1
                sheet.write(y_offset, 0, '[03] Mã số thuế: %s' % (
                    company_id.vat), get_format({'bold': True}))
                y_offset += 1
                sheet.write(y_offset, 0, '[04] Tên đại lý thuế (nếu có): %s' % (
                    ''), get_format({'bold': True}))
                y_offset += 1
                sheet.write(y_offset, 0, '[05] Mã số thuế: %s' % (
                    ''), get_format({'bold': True}))
                y_offset += 1
                sheet.merge_range(y_offset, 0, y_offset, 14, 'Đơn vị tiền: Đồng Việt Nam', get_format(
                    {'italic': True, 'align': 'right'}))
                y_offset += 2
                sheet.merge_range(y_offset, 0, y_offset+1, 0,
                                  "STT", get_format(table_border_head))
                sheet.merge_range(
                    y_offset, 1, y_offset, 4, "Hoá đơn, chứng từ nộp thuế", get_format(table_border_head))
                sheet.write(y_offset+1, 1, 'Mẫu số',
                            get_format(table_border_head))
                sheet.write(y_offset+1, 2, 'Ký hiệu',
                            get_format(table_border_head))
                sheet.write(y_offset+1, 3, 'Số', get_format(table_border_head))
                sheet.write(y_offset+1, 4, 'Ngày, tháng, năm',
                            get_format(table_border_head))
                sheet.merge_range(y_offset, 5, y_offset+1, 5,
                                  "Tên người bán", get_format(table_border_head))
                sheet.merge_range(
                    y_offset, 6, y_offset+1, 6, "Mã số thuế người bán", get_format(table_border_head))
                sheet.merge_range(
                    y_offset, 7, y_offset+1, 7, "Tên hàng hóa, dịch vụ", get_format(table_border_head))
                sheet.merge_range(y_offset, 8, y_offset+1, 8,
                                  "Đơn vị tính", get_format(table_border_head))
                sheet.merge_range(y_offset, 9, y_offset+1, 9,
                                  "Số lượng", get_format(table_border_head))
                sheet.merge_range(y_offset, 10, y_offset+1,
                                  10, "Đơn giá", get_format(table_border_head))
                sheet.merge_range(y_offset, 11, y_offset+1, 11,
                                  "Giá trị HHDV mua vào chưa có thuế GTGT", get_format(table_border_head))
                sheet.merge_range(y_offset, 12, y_offset+1, 12,
                                  "Thuế suất (%)", get_format(table_border_head))
                sheet.merge_range(y_offset, 13, y_offset+1, 13,
                                  "Tiền thuế GTGT", get_format(table_border_head))
                sheet.merge_range(y_offset, 14, y_offset+1,
                                  14, "Ghi chú", get_format(table_border_head))

                y_offset += 2
                row = y_offset
                lines = self.get_lines(o)
                total_amount = 0
                total_tax_amount = 0
                for ind, line in enumerate(lines):
                    for col in cols:
                        if col == 'stt':
                            sheet.write(row, cols[col], ind + 1,
                                        table_border_body)
                        elif col == 'note':
                            sheet.write(row, cols[col], '',
                                        table_border_body)
                        elif col == 'tax_id':
                            tax_list = line.tax_ids.mapped('amount')
                            tax_str = ', '.join(str(int(tax))
                                                for tax in tax_list)
                            sheet.write(row, cols[col], tax_str,
                                        table_border_body)
                        elif col == 'tax_amount':
                            tax_list = line.tax_ids.mapped('amount')
                            tax_amount = 0
                            for tax in tax_list:
                                tax_amount += line.price_subtotal * tax / 100
                            sheet.write(row, cols[col], tax_amount,
                                        table_border_body)
                            total_tax_amount += tax_amount
                        else:
                            write_val = safe_eval('line.%s' %
                                                  col, {'line': line}, mode='eval')
                            if col == 'price_subtotal':
                                total_amount += write_val
                            if col in ['move_id.invoice_date']:
                                if write_val:
                                    write_val = write_val.strftime(
                                        DEFAULT_SERVER_DATE_FORMAT)
                            sheet.write(row, cols[col], write_val,
                                        table_border_body)
                    row += 1
            sheet.merge_range(row, 0, row, 10, 'Tổng cộng',
                              get_format({'font_size': 12, 'bold': True, 'align': 'center', 'border': True}))
            sheet.write(row, 11, total_amount, table_border_body)
            sheet.write(row, 12, '', get_format({'font_size': 12, 'bold': True, 'align': 'center', 'border': True}))
            sheet.write(row, 13, total_tax_amount, table_border_body)
            sheet.write(row, 14, '', get_format({'font_size': 12, 'bold': True, 'align': 'center', 'border': True}))
            # footer
            row += 2
            sheet.merge_range(row, 0, row, 14, 'Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật về số liệu đã khai./.', get_format(
                {'font_size': 12, 'italic': True}))
            row += 2
            sheet.merge_range(row, 0, row, 3, 'NHÂN VIÊN ĐẠI LÝ THUẾ', get_format(
                {'font_size': 12, 'bold': True, 'align': 'center'}))
            sheet.merge_range(row, 10, row, 14, '..................., %s' % (datetime.now().strftime("ngày %d tháng %m năm %Y")), get_format(
                {'font_size': 12, 'bold': True, 'align': 'center'}))
            row += 1
            sheet.merge_range(row, 0, row, 3, 'Họ và tên', get_format(
                {'font_size': 12, 'bold': False, 'align': 'center'}))
            sheet.merge_range(row, 10, row, 14, 'NGƯỜI NỘP THUẾ hoặc', get_format(
                {'font_size': 12, 'bold': True, 'align': 'center'}))
            row += 1
            sheet.merge_range(row, 0, row, 3, 'Chứng chỉ hành nghề số', get_format(
                {'font_size': 12, 'bold': False, 'align': 'center'}))
            sheet.merge_range(row, 10, row, 14, 'ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ', get_format(
                {'font_size': 12, 'bold': True, 'align': 'center'}))
            row += 1
            sheet.merge_range(row, 10, row, 14, '(Ký, ghi rõ họ tên; chức vụ và đóng dấu (nếu có)', get_format(
                {'font_size': 12, 'italic': True, 'align': 'center'}))

    def get_lines(self, o):
        domain = [
            ('state', '=', 'posted'),
            ('journal_id.type', '=', 'purchase'),
            ('date', '>=', o.date_from),
            ('date', '<=', o.date_to),
        ]

        move_ids = self.env['account.move'].search(domain)

        return move_ids.invoice_line_ids.filtered(
            lambda l: l.tax_ids and any(t.type_tax_use == 'purchase' for t in l.tax_ids)
        )

    def check_tag(self, tax_ids, tags):
        if any(tax.id in tags for tax in tax_ids):
            return True

        return False
