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
    'direct_debit': 15,
    # for debug purpose
    'debug_group': 16 
}


class DebitAndCreditControlListReport(models.AbstractModel):
    _name = 'report.tlip_account.report_debit_credit_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Debit And Credit Control List Report'

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

        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman',
                            'font_size': 12, 'valign': 'vcenter', 'align': 'left'}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)

        sheet = workbook.add_worksheet("BKĐR")
        # sheet.hide_gridlines(2)
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 20)
        sheet.set_column(12, 12, 20)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 20)
        sheet.set_column(15, 15, 20)
        sheet.set_column(16, 16, 20)

        company_id = self.env.company
        y_offset = 0
        company_id = self.env.company
        sheet.write(y_offset, 0, '%s' % (
                    company_id.name), get_format({'bold': True}))
        y_offset += 1
        sheet.write(y_offset, 0, 'Địa chỉ: %s' % (
            self.get_company_address(company_id)), get_format({'bold': True}))
        y_offset += 2
        sheet.merge_range(y_offset, 0, y_offset, 10, 'BẢNG THEO DÕI CÔNG NỢ PHẢI THU/ DEBT AND CREDIT CONTROL LIST', get_format(
            {'font_size': 16, 'bold': True, 'align': 'center'}))
        y_offset += 1
        sheet.merge_range(y_offset, 0, y_offset, 10, 'Từ ngày: %s   Đến ngày: %s' % (o.from_date, o.to_date), get_format(
            {'font_size': 12, 'bold': True, 'align': 'center'}))
        y_offset += 2
        # header table
        sheet.merge_range(y_offset, 0, y_offset + 1, 0, 'Mã khách hàng',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 1, y_offset + 1, 1, 'Tên khách hàng',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 2, y_offset + 1, 2, 'Diễn giải',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 3, y_offset, 9, 'Thông tin phải thu',
                          get_format(table_border_head))  # merge 7 columns
        sheet.write(y_offset + 1, 3, 'Số đề nghị thanh toán',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 4, 'Ngày đề nghị thanh toán',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 5, 'Hạn thanh toán',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 6, 'Số hóa đơn',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 7, 'Ngày phát hành',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 8, 'Đơn vị tiền tệ',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 9, 'Số tiền ĐNTT',
                    get_format(table_border_head))
        sheet.merge_range(y_offset, 10, y_offset, 11, 'Thanh toán',
                          get_format(table_border_head))  # merge 2 columns
        sheet.write(y_offset + 1, 10, 'Số tiền',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 11, 'Ngày',
                    get_format(table_border_head))
        sheet.merge_range(y_offset, 12, y_offset + 1, 12, 'Số tiền còn nợ',
                          get_format(table_border_head))
        sheet.merge_range(y_offset, 13, y_offset, 14, 'Nợ quá hạn',
                          get_format(table_border_head))
        sheet.write(y_offset + 1, 13, 'Số tiền',
                    get_format(table_border_head))
        sheet.write(y_offset + 1, 14, 'Ngày',
                    get_format(table_border_head))
        sheet.merge_range(y_offset, 15, y_offset + 1, 15, 'Direct debit',
                          get_format(table_border_head))
        # for debug purpose
        sheet.merge_range(y_offset, 16, y_offset + 1, 16, 'Nhóm dữ liệu (Debug)',
                          get_format(table_border_head))
        y_offset += 2

        request_types = self.get_grouped_lines(o)
        row = y_offset
        for type in request_types:
            # write request type and total
            sheet.write(row, 0, 'Total', table_border_body)
            sheet.merge_range(row, 1, row, 8, '%s' % (type[1]['request_type']), get_format(
                {'bold': True, 'font_size': 12, 'align': 'left'}))
            sheet.write(row, 9, type[1]['total'], table_border_body_number)
            for col in ['payment_amount', 'outstanding_amount', 'overdue_amount']:
                sheet.write(row, cols[col], '', table_border_body_number)
            row += 1
            for line in type[1]['lines']:
                for col in cols.keys():
                    sheet.write(row, cols[col], line[col],
                                table_border_body_number if col in ['request_payment_amount', 'payment_amount',
                                                                    'outstanding_amount', 'overdue_amount', 'overdue_date'] else table_border_body)
                row += 1

    def get_lines(self, o):
        vals = []
        today = fields.Date.context_today(self)
        # TODO check
        # Tìm ra các khoản cọc cũ nhưng được sử dụng/cấn trừ trong hoặc sau kỳ báo cáo)
        # reconciles_from_date = self.env['account.partial.reconcile'].search([
        #     ('company_id', '=', self.env.company.id),
        #     ('max_date', '>=', o.from_date)
        # ])
        
        # # Lấy ID các Payment liên quan đến các khoản đối soát này
        # reconciled_payment_ids = (
        #     reconciles_from_date.mapped('credit_move_id.payment_id').ids + 
        #     reconciles_from_date.mapped('debit_move_id.payment_id').ids
        # )

        # domain_payment = [
        #     ('approval_state', '=', 'approved'),
        #     ('state', 'in', ['draft', 'paid']),
        #     ('payment_type', '=', 'inbound'),
        #     ('is_request_payment', '=', True),
        #     ('company_id', '=', self.env.company.id),
            
        #     '|', '|',
        #         # Nhóm A: Khoản đặt cọc/thanh toán phát sinh TRONG kỳ
        #         '&', ('date', '>=', o.from_date), ('date', '<=', o.to_date),
                
        #         # Nhóm B: Đặt cọc cũ (trước kỳ) nhưng HIỆN TẠI vẫn chưa cấn trừ hết (is_reconciled = False)
        #         '&', ('date', '<', o.from_date), ('is_reconciled', '=', False),
                
        #         # Nhóm C: Đặt cọc cũ đã cấn trừ xong, nhưng hành động cấn trừ diễn ra TRONG hoặc SAU kỳ báo cáo
        #         ('id', 'in', reconciled_payment_ids)
        # ]

        domain = [
            ('approval_state', '=', 'approved'),
            ('state', 'in', ['draft', 'paid']),
            ('payment_type', '=', 'inbound'),
            ('is_request_payment', '=', True),
            ('company_id', '=', self.env.company.id),
            '|', '|',
            '&', ('date', '>=', o.from_date), ('date', '<=', o.to_date),
            '&', ('due_date', '>=', o.from_date), ('due_date', '<=', o.to_date),
            '&', ('date', '<', o.from_date), ('state', '=', 'draft')
        ]
        deposit_payment = self.env['account.payment'].search(
            domain, order="date asc")
        for payment in deposit_payment:
            is_payment_overdue = payment.due_date and payment.due_date < today
            vals.append({
                'request_type_id': payment.invoice_type_id.id,
                'request_type': payment.invoice_type_id.name_vn if self.env.user.lang == 'vi_VN' else payment.invoice_type_id.name_en or '',
                'partner_ref': payment.partner_id.ref or '',
                'partner_name': payment.partner_id.name,
                'description': payment.memo if payment.memo else 'Deposit Payment',
                'request_payment_number': payment.request_payment_number,
                'date': payment.date.strftime(DEFAULT_SERVER_DATE_FORMAT) if payment.date else '',
                'due_date': payment.due_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if payment.due_date else '',
                'invoice_no': '',
                'issue_date': '',
                'currency': payment.currency_id.name,
                'request_payment_amount': payment.amount,
                'payment_amount': payment.amount if payment.state == 'paid' else 0.0,
                'payment_date': payment.date.strftime(DEFAULT_SERVER_DATE_FORMAT) if payment.date and payment.state == 'paid' else '',
                'outstanding_amount': payment.amount if is_payment_overdue and payment.state != 'paid' else 0.0,
                'overdue_amount': payment.amount if is_payment_overdue and payment.state != 'paid' else 0.0,
                'overdue_date': (today - payment.due_date).days if is_payment_overdue and payment.state != 'paid' else '',
                'direct_debit': '',
                # for debug purpose
                'debug_group': 'Payment/Deposit (Tiền cọc)'
            })
        # Tra cứu các giao dịch đối soát (reconcile) diễn ra từ from_date đến to_date
        reconciles = self.env['account.partial.reconcile'].search([
            ('company_id', '=', self.env.company.id),
            ('max_date', '>=', o.from_date),
            ('max_date', '<=', o.to_date)
        ])
        
        # Lấy ID các hóa đơn bán ra (out_invoice) liên quan đến các khoản đối soát này
        reconciled_invoice_ids = reconciles.mapped('debit_move_id.move_id').filtered(
            lambda m: m.move_type == 'out_invoice'
        ).ids

        domain_inv = [
            ('move_type', '=', 'out_invoice'), 
            ('is_request_payment', '=', True), 
            ('company_id', '=', self.env.company.id),
            ('approval_state', '=', 'approved'),
            ('state', 'in', ['draft', 'posted']),
            ('exclude_from_debit_credit_report', '=', False),
            '|', ('invoice_type_code', '!=', 'utility'), ('utility_type', 'in', ('water', 'electricity')),
            
            '|', '|',
                # Nhóm A: Hóa đơn phát sinh TRONG kỳ báo cáo
                '&', ('create_date', '>=', o.from_date), ('create_date', '<=', o.to_date),
                
                # Nhóm B: Hóa đơn cũ (trước kỳ) nhưng HIỆN TẠI vẫn chưa trả hết (Dư nợ chuyển sang)
                '&', ('create_date', '<', o.from_date), ('payment_state', 'in', ['not_paid', 'partial']),
                
                # Nhóm C: Hóa đơn cũ (trước kỳ) đã trả xong, nhưng được thanh toán TRONG kỳ báo cáo này
                ('id', 'in', reconciled_invoice_ids)
        ]
        inv_payments = self.env['account.move'].search(domain_inv, order="create_date asc")
        
        for inv in inv_payments:
            invoice_payments = inv.invoice_payments_widget['content'] if inv.invoice_payments_widget else []
            # Lọc các khoản thanh toán chỉ nằm trong đến ngày (to_date)
            valid_payments = [p for p in invoice_payments if p['date'] <= o.to_date]
            
            invoice_payments_amount = sum(p['amount'] for p in valid_payments)
            inv_payment_date = max(p['date'] for p in valid_payments) if valid_payments else False
            
            is_overdue_invoice = inv.invoice_date_due and inv.invoice_date_due < today

            # --- for DEBUG ---
            debug_group = 'Chưa xác định'
            report_date = fields.Date.to_date(inv.create_date) if inv.create_date else False
            if report_date:
                if report_date < o.from_date:
                    if inv.payment_state in ['not_paid', 'partial']:
                        debug_group = 'Nhóm B (Nợ cũ tồn đọng)'
                    elif inv.id in reconciled_invoice_ids:
                        debug_group = 'Nhóm C (Nợ cũ trả trong kỳ)'
                elif o.from_date <= report_date <= o.to_date:
                    debug_group = 'Nhóm A (Phát sinh trong kỳ)'
            # --------------------------------------------

            vals.append({
                'request_type_id': inv.invoice_type_id.id,
                'request_type': inv.invoice_type_id.name_vn if self.env.user.lang == 'vi_VN' else inv.invoice_type_id.name_en or '',
                'partner_ref': inv.partner_id.ref or '',
                'partner_name': inv.partner_id.name,
                'description': '; '.join(filter(None, inv.invoice_line_ids.mapped('name'))),
                'request_payment_number': inv.request_payment_number,
                'date': report_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if report_date else '',
                'due_date': inv.invoice_date_due.strftime(DEFAULT_SERVER_DATE_FORMAT) if inv.invoice_date_due else '',
                'invoice_no': inv.einvoice_no or '',
                'issue_date': inv.invoice_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if inv.invoice_date else '',
                'currency': inv.currency_id.name,
                'request_payment_amount': inv.amount_total,
                'payment_amount': invoice_payments_amount or 0.0,
                'payment_date': inv_payment_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if inv_payment_date else '',
                'outstanding_amount': inv.amount_residual or 0.0,
                'overdue_amount': inv.amount_residual if is_overdue_invoice else 0.0,
                'overdue_date': is_overdue_invoice and (today - inv.invoice_date_due).days or '',
                'direct_debit': '',
                # for debug purpose
                'debug_group': debug_group
            })
        return vals

    def get_grouped_lines(self, o):
        lines = self.get_lines(o)
        values = {}
        for line in lines:
            if line['request_type_id'] not in values:
                values[line['request_type_id']] = {
                    'request_type': line['request_type'],
                    'lines': [{k: line[k] for k in cols.keys()}],
                    'total': line['request_payment_amount']
                }
            else:
                values[line['request_type_id']]['lines'].append(
                    {k: line[k] for k in cols.keys()})
                values[line['request_type_id']
                       ]['total'] += line['request_payment_amount']
        return values.items()
