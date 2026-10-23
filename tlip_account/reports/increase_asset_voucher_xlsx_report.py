from odoo import models, fields, _


class increase_asset_voucher_xlsx(models.AbstractModel):
    _name = 'report.tlip_account.increase_asset_voucher_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'increase_asset_voucher_xlsx'

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
        sheet = workbook.add_worksheet(_("Increase Asset Voucher"))
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 4, 15)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 25)

        sheet.set_default_row(20)
        sheet.hide_gridlines(2)

        sheet.merge_range(0, 0, 0, 6,
                          company.name, get_format({'bold': True}))
        sheet.merge_range(1, 0, 1, 6,
                          self.get_company_address(company),
                          get_format({'font_size': 12}))
        sheet.merge_range(2, 0, 2, 6,
                          "PHIẾU TĂNG TÀI SẢN TỪ XDCB\n(Increase Asset Voucher)",
                          get_format({'font_size': 15, 'bold': True, 'align': 'center'}))
        sheet.set_row(2, 35)

        sheet.write(3, 4, 'Số chứng từ\n(Voucher No.)',
                    get_format({'font_size': 10}))
        sheet.write(3, 5, '', get_format({}))
        sheet.set_row(3, 25)
        sheet.merge_range(4, 4, 4, 5,
                          f"Ngày  {today.day}  tháng  {today.month}  năm  {today.year}\n(Date)   (month)   (year)",
                          get_format({'font_size': 10}))
        sheet.set_row(4, 25)
        sheet.merge_range(5, 0, 5, 6,
                          f"Đơn vị NCC: {objs.asset_supplier_id.name or ''}",
                          get_format({'align': 'left'}))
        sheet.merge_range(6, 0, 6, 2,
                          f"Mã tài sản: {objs.asset_code or ''}",
                          get_format({'align': 'left'}))
        sheet.merge_range(6, 3, 6, 6,
                          f"Tên tài sản: {objs.name}",
                          get_format({'align': 'left'}))
        sheet.merge_range(7, 0, 7, 6,
                          f"Thời gian KH/PB: {objs.method_number}",
                          get_format({'align': 'left'}))

        titles = [
            'Số Hóa Đơn\n(Invoice No.)',
            'Ngày Hóa Đơn\n(Voucher Date)',
            'Nội dung chi tiết\n(Detail)',
            'Ghi nợ\n(Debit Acc)',
            'Ghi có\n(Credit Acc)',
            'Số tiền VND\n(VND Amount)',
            'Tên khoản mục ngân sách\n(Budget Name)',
        ]
        sheet.set_row(9, 30)
        for index, title in enumerate(titles):
            sheet.write(9, index, title, get_format(table_border_head))
        row = 10
        total = 0
        increase_assets = self.env['account.asset'].search([
            ('parent_id', '=', objs.id),
            ('state', 'in', ['open', 'paused', 'close'])])
        increase_related_moves = increase_assets.mapped(
            'original_move_line_ids.move_id')
        increase_moves = increase_related_moves.filtered_domain([
            ('asset_move_type', '=', 'positive_revaluation'),
            ('state', '=', 'posted')
        ])
        for move in increase_moves:
            debit_item = move.line_ids.filtered(
                lambda line: line.debit > 0)
            credit_item = move.line_ids.filtered(
                lambda line: line.credit > 0)
            sheet.write(row, 0, move.name, get_format(table_border_body))
            sheet.write(row, 1, fields.Date.to_string(
                move.date), get_format(table_border_body, {'align': 'center'}))
            sheet.write(row, 2, debit_item.name,
                        get_format(table_border_body))
            sheet.write(row, 3, debit_item.account_id.code,
                        get_format(table_border_body, {'align': 'center'}))
            sheet.write(row, 4, credit_item.account_id.code,
                        get_format(table_border_body, {'align': 'center'}))
            sheet.write(row, 5, self.format_float_number(
                move.amount_total), get_format(table_border_body, {'align': 'right'}))
            budget_codes_str = ''
            if debit_item.analytic_distribution:
                budget_code_ids = list(
                    dict(debit_item.analytic_distribution).keys())
                budget_codes = self.env['account.analytic.account'].sudo().browse(
                    budget_code_ids)
                budget_codes_str = ','.join(budget_codes.mapped('code'))
            sheet.write(row, 6, budget_codes_str,
                        get_format(table_border_body))
            total += move.amount_total
            row += 1

        sheet.write(row, 0, 'Tổng cộng (Total)',
                    get_format(table_border_head))
        sheet.write(row, 1, '', get_format(table_border_body))
        sheet.write(row, 2, '', get_format(table_border_body))
        sheet.write(row, 3, '', get_format(table_border_body))
        sheet.write(row, 4, '', get_format(table_border_body))
        sheet.write(row, 5, self.format_float_number(total),
                    get_format(table_border_head, {'align': 'right'}))
        sheet.write(row, 6, '', get_format(table_border_body))
        row += 1
        amount_in_words_en = company.currency_id.with_context(lang='en_US').amount_to_text(
            total).capitalize().replace('dong', 'vietnamese dong')
        amount_in_words_vn = company.currency_id.with_context(lang='vi_VN').amount_to_text(
            total).capitalize().replace('dong', 'đồng')
        sheet.merge_range(row, 0, row, 6, f'Số tiền bằng chữ: {amount_in_words_vn}',
                          get_format({'font_size': 12}))
        sheet.merge_range(row + 1, 0, row + 1, 6, f'(Amount in words): {amount_in_words_en}',
                          get_format({'italic': True, 'font_size': 11}))
        row += 2
        sheet.merge_range(row, 0, row, 1, 'Người lập',
                          get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(row, 2, row, 3, 'Kế toán trưởng',
                          get_format({'bold': True, 'align': 'center'}))
        sheet.merge_range(row, 4, row, 5, 'Được duyệt bởi',
                          get_format({'bold': True, 'align': 'center'}))
        row += 1
        sheet.merge_range(row, 0, row, 1, '(Prepared by)', get_format(
            {'italic': True, 'align': 'center'}))
        sheet.merge_range(row, 2, row, 3, '(Chief Accountant)', get_format(
            {'italic': True, 'align': 'center'}))
        sheet.merge_range(row, 4, row, 5, '(Approved)', get_format(
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
