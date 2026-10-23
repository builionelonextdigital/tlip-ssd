from odoo import models, fields, _


class accounting_voucher_xlsx(models.AbstractModel):
    _name = 'report.tlip_account.accounting_voucher_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'accounting_voucher_xlsx'

    def generate_xlsx_report(self, workbook, data, objs):
        self = self.with_context(lang=self.env.user.lang)
        table_border_head = {
            'font_name': 'Times New Roman', 'font_size': 12, 'text_wrap': True,
            'align': 'center', 'border': True, 'bold': True
        }
        table_border_body = {'font_name': 'Times New Roman', 'font_size': 12,
                             'align': 'left', 'top': True, 'bottom': True, 'left': True, 'right': True}

        def get_format(*arguments):
            normal_style = {'font_name': 'Times New Roman', 'font_size': 12,
                            'valign': 'vcenter', 'align': 'left', 'text_wrap': True}
            for arg in arguments:
                normal_style.update(arg)
            return workbook.add_format(normal_style)

        company = self.env.company
        today = fields.Date.today()
        sheet = workbook.add_worksheet(_("Accounting Voucher"))
        sheet.set_column(0, 1, 15)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 5, 15)
        sheet.set_column(6, 8, 20)
        sheet.set_column(9, 11, 25)

        sheet.set_default_row(20)
        sheet.hide_gridlines(2)

        sheet.merge_range(0, 0, 0, 11,
                          company.name, get_format({'bold': True}))
        sheet.merge_range(1, 0, 1, 11,
                          self.get_company_address(company),
                          get_format({}))
        sheet.merge_range(2, 0, 2, 11,
                          "PHIẾU HẠCH TOÁN\n(Accounting Voucher)",
                          get_format({'font_size': 15, 'bold': True, 'align': 'center'}))
        sheet.set_row(2, 35)

        sheet.write(3, 5, 'Số chứng từ\n(Voucher No.)',
                    get_format({'font_size': 10}))
        sheet.write(3, 6, '', get_format({}))
        sheet.set_row(3, 25)
        sheet.merge_range(4, 5, 4, 7,
                          f"Ngày  {today.day}  tháng  {today.month}  năm  {today.year}\n(Date)   (month)   (year)",
                          get_format({'font_size': 10}))
        sheet.set_row(4, 25)

        titles = [
            'Số Hóa Đơn\n(Invoice No.)',
            'Ngày Hóa Đơn\n(Voucher Date)',
            'Đơn vị NCC\n(Supplier)',
            'Nội dung chi tiết\n(Detail)',
            'Ghi nợ\n(Debit Acc)',
            'Ghi có\n(Credit Acc)',
            'Số tiền VND\n(VND Amount)',
            'Nguyên tệ\n(Amount Currency)',
            'Tỷ giá\n(Exchange Rate)',
            'Tên khoản mục ngân sách\n(Budget Name)',
            'Mã tài sản\n(CCDC/SER)',
            'TG phân bổ\n(Allocation time)',
        ]
        sheet.set_row(6, 30)
        for index, title in enumerate(titles):
            sheet.write(6, index, title, get_format(table_border_head))
        row = 7
        total = 0
        for item in objs:
            move = item.move_id
            account_type = 'asset_receivable' if move.is_sale_document(
                include_receipts=True) else 'liability_payable'
            counterpart_item = move.line_ids.filtered(
                lambda line: line.account_type == account_type)
            counterpart_account = counterpart_item.account_id.code if counterpart_item else ''
            sheet.write(row, 0, move.name, get_format(table_border_body))
            sheet.write(row, 1, fields.Date.to_string(
                item.date), get_format(table_border_body, {'align': 'center'}))
            sheet.write(row, 2, item.partner_id.name or '',
                        get_format(table_border_body))
            sheet.write(row, 3, item.name, get_format(table_border_body))
            sheet.write(row, 4, item.account_id.code,
                        get_format(table_border_body, {'align': 'center'}))
            sheet.write(row, 5, counterpart_account,
                        get_format(table_border_body, {'align': 'center'}))
            sheet.write(row, 6, self.format_float_number(
                abs(item.balance)), get_format(table_border_body, {'align': 'right'}))
            sheet.write(row, 7, abs(item.amount_currency) if item.currency_id != company.currency_id else '',
                        get_format(table_border_body, {'align': 'right'}))
            sheet.write(row, 8, move.entry_currency_rate if item.currency_id != company.currency_id else '',
                        get_format(table_border_body, {'align': 'right'}))
            budget_codes_str = ''
            if item.analytic_distribution:
                budget_code_ids = [int(id) for id in dict(item.analytic_distribution).keys()]
                budget_codes = self.env['account.analytic.account'].sudo().browse(
                    budget_code_ids)
                budget_codes_str = ','.join(budget_codes.mapped('code'))
            sheet.write(row, 9, budget_codes_str,
                        get_format(table_border_body))
            sheet.write(row, 10, move.asset_id.asset_code if move.asset_id else '',
                        get_format(table_border_body))
            sheet.write(row, 11, move.asset_id.method_number if move.asset_id else '',
                        get_format(table_border_body))
            total += abs(item.balance)
            row += 1

        sheet.write(row, 0, 'Tổng cộng (Total)',
                    get_format(table_border_head))
        sheet.write(row, 1, '', get_format(table_border_body))
        sheet.write(row, 2, '', get_format(table_border_body))
        sheet.write(row, 3, '', get_format(table_border_body))
        sheet.write(row, 4, '', get_format(table_border_body))
        sheet.write(row, 5, '', get_format(table_border_body))
        sheet.write(row, 6, self.format_float_number(total),
                    get_format(table_border_head, {'align': 'right'}))
        sheet.write(row, 7, '', get_format(table_border_body))
        sheet.write(row, 8, '', get_format(table_border_body))
        sheet.write(row, 9, '', get_format(table_border_body))
        sheet.write(row, 10, '', get_format(table_border_body))
        sheet.write(row, 11, '', get_format(table_border_body))
        row += 1
        amount_in_words_en = company.currency_id.with_context(lang='en_US').amount_to_text(
            total).capitalize().replace('dong', 'vietnamese dong')
        amount_in_words_vn = company.currency_id.with_context(lang='vi_VN').amount_to_text(
            total).capitalize().replace('dong', 'đồng')
        sheet.merge_range(row, 0, row, 11, f'Số tiền bằng chữ: {amount_in_words_vn}',
                          get_format({'font_size': 12}))
        sheet.merge_range(row + 1, 0, row + 1, 11, f'(Amount in words): {amount_in_words_en}',
                          get_format({'italic': True, 'font_size': 11}))
        row += 2
        sheet.merge_range(row, 0, row, 2, 'Người lập',
                          get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(row, 3, row, 4, 'Kế toán trưởng',
                          get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(row, 6, row, 8, 'Được duyệt bởi',
                          get_format({'bold': True, 'align': 'center'}))
        row += 1
        sheet.merge_range(row, 0, row, 2, '(Prepared by)', get_format(
            {'italic': True, 'align': 'center'}))
        sheet.merge_range(row, 3, row, 4, '(Chief Accountant)', get_format(
            {'italic': True, 'align': 'center'}))
        sheet.merge_range(row, 6, row, 8, '(Approved)', get_format(
            {'italic': True, 'align': 'center'}))

    def get_company_address(self, company):
        arr_address = []
        if company.street:
            arr_address.append(company.street)
        if company.street2:
            arr_address.append(company.street2)
        if company.city:
            arr_address.append(company.city)
        if company.state_id:
            arr_address.append(company.state_id.name)
        if company.country_id:
            arr_address.append(company.country_id.name)
        return ', '.join(arr_address)

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
