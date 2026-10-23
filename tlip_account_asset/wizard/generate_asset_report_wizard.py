import base64
import calendar
from collections import defaultdict
from datetime import date
import io
import re
from odoo import api, fields, models, _
from odoo.tools import SQL
from odoo.tools.misc import xlsxwriter, format_date


class GenerateAssetReportWizard(models.TransientModel):
    _name = 'generate.asset.report.wizard'
    _description = 'Generate Asset Report Wizard'

    def _get_month_selection(self):
        return [(str(i), str(i).zfill(2)) for i in range(1, 13)]

    def _get_year_selection(self):
        current_year = fields.Datetime.now().year
        return [(str(i), str(i)) for i in range(current_year - 10, current_year + 11)]

    month = fields.Selection(
        selection=_get_month_selection, string="Month",
        default=str(fields.Datetime.now().month), required=True)
    year = fields.Selection(selection=_get_year_selection,
                            default=str(fields.Datetime.now().year),
                            string="Year", required=True)
    binary_file = fields.Binary()
    filename = fields.Char()
    report = fields.Selection([
        ('depreciation_fixed_assets', 'DEPRECIATION FOR FIXED ASSETS'),
        ('fixed_assets_registration', 'FIXED ASSET REGISTRATION'),
        ('allocation_equipment_expenses', 'ALLOCATION OF EQUIPMENT AND PREPAID EXPENSES')])

    def _get_month_start_end(self):
        self.ensure_one()
        month = int(self.month)
        year = int(self.year)
        end_day_of_month = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = start_date.replace(day=end_day_of_month)
        return start_date, end_date

    def _where_assets_expense_query(self, to_date):
        asset_types = ['fixed_asset']
        if self.report == 'allocation_equipment_expenses':
            asset_types = ['expense']
        return SQL('''
        WHERE aa.state = 'open' AND aa.acquisition_date < %(to_date)s
            AND aa.parent_id is null AND aa.asset_type IN %(asset_types)s
            AND aa.company_id IN %(company_id)s
        ''', to_date=to_date, asset_types=tuple(asset_types), company_id=tuple(self.env.companies.ids))

    def _collect_assets_expense_query(self, from_date, to_date):
        where_clause = self._where_assets_expense_query(to_date)
        query = SQL('''
        SELECT aa.id, aa.name, aa.acquisition_date, maa.name AS model,
            aa.prorata_date, aa.asset_code,
            CASE
                WHEN aa.method_period = '1' THEN aa.method_number
                ELSE aa.method_number * 12
            END as depreciation_months,
            aa.original_value AS opening_original_value,
            SUM(am.depreciation_value) AS already_depreciation
        FROM account_asset aa
            LEFT JOIN account_asset maa ON maa.id = aa.model_id
            LEFT JOIN account_move am ON am.asset_id = aa.id
                AND am.state = 'posted' AND am.date < %(from_date)s
                AND am.asset_move_type = 'depreciation'
        %(where_clause)s
        GROUP BY aa.id, maa.id
        ORDER BY aa.asset_type, maa.name
        ''', from_date=from_date, to_date=to_date, where_clause=where_clause)
        return query

    def _collect_assets_expense_data(self, report_type=''):
        from_date, to_date = self._get_month_start_end()
        asset_env = self.env['account.asset']
        query = self._collect_assets_expense_query(from_date, to_date)
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        for data in datas:
            asset = asset_env.browse(data['id'])
            depreciation_moves = asset.depreciation_move_ids
            increase_assets = asset_env.search([
                ('parent_id', '=', data['id']),
                ('state', 'in', ['open', 'paused', 'close']),
                ('acquisition_date', '<=', to_date),
                ('revaluation_reason_id.type', '=', 'increase')
            ])
            opening_increase_assets = increase_assets.filtered_domain([
                ('acquisition_date', '<', from_date),
            ])
            period_increase_assets = increase_assets.filtered_domain([
                ('acquisition_date', '>=', from_date),
            ])
            
            increase_related_moves = increase_assets.mapped('depreciation_move_ids').filtered_domain([
                ('state', '!=', 'cancel'),
                # ('date', '>=', from_date),
                ('date', '<=', to_date)
            ])
            # decrease_assets = asset_env.search([
            #     ('parent_id', '=', data['id']),
            #     ('state', 'in', ['open', 'paused', 'close']),
            #     ('acquisition_date', '<=', to_date),
            #     ('revaluation_reason_id.type', '=', 'decrease')
            # ])
            # decrease_related_moves = decrease_assets.mapped('depreciation_move_ids').filtered_domain([
            #     ('state', '!=', 'cancel'),
            #     # ('date', '>=', from_date),
            #     ('date', '<=', to_date)
            # ])
            increase_moves = depreciation_moves.filtered_domain([
                ('state', '!=', 'cancel'),
                ('asset_move_type', '!=', 'negative_revaluation'),
                ('date', '>=', from_date),
                ('date', '<=', to_date)
            ])
            negative_revaluation_moves = depreciation_moves.filtered_domain([
                ('asset_move_type', '=', 'negative_revaluation'),
                ('state', '=', 'posted'),
                ('date', '>=', from_date),
                ('date', '<=', to_date)
            ])
            decrease_depreciation_moves = depreciation_moves.filtered_domain([
                ('asset_move_type', '=', 'depreciation'),
                ('state', '=', 'posted'),
                ('depreciation_value', '<', 0),
                ('date', '>=', from_date),
                ('date', '<=', to_date)
            ])
            opening_decrease_moves = depreciation_moves.filtered_domain([
                ('asset_move_type', '=', 'negative_revaluation'),
                ('state', '=', 'posted'),
                ('date', '<', from_date)
            ])
            opening_original_value = (
                (data.get('opening_original_value') or 0.0)
                + sum(opening_increase_assets.mapped('original_value'))
                - sum(opening_decrease_moves.mapped('amount_total'))
            )
            increase_original_value = sum(
                period_increase_assets.mapped('original_value'))
            decrease_original_value = sum(
                negative_revaluation_moves.mapped('amount_total'))
            already_depreciation = data.get('already_depreciation') or 0.0
            already_depreciation += asset.already_depreciated_amount_import
            # update modified depreciation amount(
            related_already_depreciation = sum(increase_related_moves.filtered_domain([('date', '<', to_date)]).mapped('amount_total'))
            increase_related_moves = sum(increase_related_moves.filtered_domain([('date', '>=', from_date), ('date', '<=', to_date)]).mapped('amount_total'))
            # decrease_related_moves = sum(decrease_related_moves.mapped('amount_total'))
            already_depreciation += related_already_depreciation if report_type in ['depreciation_fixed_assets', 'allocation_equipment_expenses'] else 0.0
            increase_depreciation = sum(increase_moves.mapped('amount_total')) + increase_related_moves if report_type in ['depreciation_fixed_assets', 'allocation_equipment_expenses'] else 0.0
            decrease_depreciation = sum(
                abs(amount) for amount in
                decrease_depreciation_moves.mapped('depreciation_value'))
            ending_original_value = (
                opening_original_value
                + increase_original_value
                - decrease_original_value
            )
            ending_depreciation = already_depreciation + \
                increase_depreciation - decrease_depreciation
            analytic_accounts = asset.mapped(
                'depreciation_line_ids.analytic_account_id')
            account_allocation = asset.mapped(
                'depreciation_line_ids.account_depreciation_expense_id')
            data.update({
                'acquisition_date': format_date(self.env, fields.Date.to_string(asset.acquisition_date)),
                'asset_group_id': asset.asset_group_id.id,
                'asset_group_name': asset.asset_group_id.name or 'No Group',
                'asset_group_prefix': asset.asset_group_id.asset_prefix or '',
                'asset_model_id': asset.model_id.id,
                'asset_model_name': asset.model_id.name or 'No Group',
                'opening_original_value': opening_original_value,
                'increase_original_value': increase_original_value,
                'decrease_original_value': decrease_original_value,
                'ending_original_value': ending_original_value,
                'already_depreciation': already_depreciation,
                # 'related_already_depreciation': related_already_depreciation,
                # 'increase_related_moves': increase_related_moves,
                # 'decrease_related_moves': decrease_related_moves,
                'increase_depreciation': increase_depreciation,
                'decrease_depreciation': decrease_depreciation,
                'ending_depreciation': ending_depreciation,
                'remaining_value': ending_original_value - ending_depreciation,
                'account_asset': asset.account_asset_id.code,
                'account_depreciation': asset.account_depreciation_id.code,
                'budget_code': ','.join(analytic_accounts.mapped('code')),
                'budget_name': ','.join(analytic_accounts.mapped('name')),
                'account_allocation': ','.join([acc.code if acc.code else '' for acc in account_allocation]) if account_allocation else ''
            })
        if report_type == 'depreciation_fixed_assets':
            datas.sort(key=lambda data: (
                not data['asset_group_id'],
                data['asset_group_name'],
                data.get('asset_code') or '',
            ))
        elif report_type == 'allocation_equipment_expenses':
            datas.sort(key=lambda data: (
                not data['asset_model_id'],
                data['asset_model_name'],
                data.get('asset_code') or '',
            ))
        return datas

    def _parse_data_depreciation_fixed_assets(self, report_type):
        datas = self._collect_assets_expense_data(report_type)
        title_vi = 'BẢNG TÍNH KHẤU HAO TÀI SẢN CỐ ĐỊNH'
        title_en = 'DEPRECIATION FOR FIXED ASSETS'
        table_titles = [
            ["Mã TSCĐ / Code of Asset", 'A7:A8', True],
            ["Tên TSCĐ / Name of Asset", 'B7:B8', True],
            ["Ngày đưa vào SD / Start using date", 'C7:C8', True],
            ["Số tháng khấu hao / Months of depreciation", 'D7:D8', True],
            ["Nguyên giá / Original Value", 'E7:H7', True],
            ["GT khấu hao / Depreciation amount", 'I7:L7', True],
            ["Giá trị còn lại / Remaining Value", 'M7:M8', True],
            ["TK khấu hao nợ / Depreciation Debit Acc", 'N7:N8', True],
            ["TK khấu hao có / Depreciation Cre Acc", 'O7:O8', True],
            ["TK TSCD / FA Acc", 'P7:P8', True],
            ["Mã KM / Budget code", 'Q7:Q8', True],
            ["Tên KM / Budget name", 'R7:R8', True],
            ["Nguyên giá đầu kỳ / Opening Original Value", 'E8', False],
            ["Tăng Nguyên giá / Increase Original Value", 'F8', False],
            ["Giảm Nguyên giá / Decrease Original Value", 'G8', False],
            ["Nguyên giá cuối kỳ / Closing Original Value", 'H8', False],
            ["Khấu hao đầu kỳ / Opening accumulated depreciation", 'I8', False],
            ["Tăng Khấu hao / Increase depreciation", 'J8', False],
            ["Giảm Khấu hao / Decrease depreciation", 'K8', False],
            ["Khấu hao cuối kỳ / Ending accumulated depreciation", 'L8', False]
        ]
        keys = ['asset_code', 'name', 'acquisition_date', 'depreciation_months',
                'opening_original_value', 'increase_original_value', 'decrease_original_value',
                'ending_original_value', 'already_depreciation', 'increase_depreciation', 'decrease_depreciation',
                'ending_depreciation', 'remaining_value', 'account_asset', 'account_depreciation',
                'account_allocation', 'budget_code', 'budget_name']
        return title_vi, title_en, table_titles, datas, 19, keys

    def _parse_data_fixed_assets_registration(self, worksheet, format):
        from_date, to_date = self._get_month_start_end()
        asset_dict = defaultdict(dict)
        increase_reasons = self.env['asset.revaluation.reason'].search(
            [('type', '=', 'increase')])
        decrease_reasons = self.env['asset.revaluation.reason'].search(
            [('type', '=', 'decrease')])
        disposal_moves = self.env['account.move'].search([
            ('asset_move_type', '=', 'disposal'),
            ('state', '!=', 'cancel'),
            ('date', '>=', from_date),
            ('date', '<=', to_date)
        ])
        running_assets = self.env['account.asset'].search([
            ('state', 'in', ['open', 'paused', 'close']),
            ('parent_id', '=', False),
            ('acquisition_date', '>=', from_date),
            ('acquisition_date', '<=', to_date)])
        for move in disposal_moves:
            asset = move.asset_id
            if asset.asset_type != 'fixed_asset':
                continue
            reason_id = move.revaluation_reason_id.id
            asset_dict[asset.id][reason_id] = move.amount_total + \
                asset_dict[asset.id].get(reason_id, 0)
        for asset in running_assets:
            if asset.asset_type != 'fixed_asset':
                continue
            reason_id = asset.revaluation_reason_id.id
            asset_dict[asset.id][reason_id] = asset.original_value + \
                asset_dict[asset.id].get(reason_id, 0)
        title_vi = 'DANH SÁCH BIẾN ĐỘNG TSCĐ'
        title_en = 'FIXED ASSET REGISTRATION'
        table_titles = [
            "Mã TSCĐ / Code of Asset",
            "Tên TSCĐ / Description",
            "Số lượng / Unit",
            "Ngày bắt đầu sử dụng / Start using date",
            "Thời gian sử dụng / Usage time (month)"
        ]

        # Parse title of table
        col = 0
        header_bold = format.get('header_bold')
        for title_name in table_titles:
            worksheet.merge_range(6, col, 7, col,
                                  title_name, header_bold)
            col += 1
        merge_col = col
        for i_reason in increase_reasons:
            worksheet.write(7, col, i_reason.name, header_bold)
            col += 1
        worksheet.write(
            7, col, "Ngày mua / Date of Purchase", header_bold)
        worksheet.write(
            7, col + 1,
            "Nhà cung cấp / Supplier", header_bold)
        worksheet.merge_range(6, merge_col, 6, col + 1,
                              "Chi tiết tăng / Increasing Detail", header_bold)
        col += 2
        merge_col = col
        for d_reason in decrease_reasons:
            worksheet.write(7, col, d_reason.name, header_bold)
            col += 1
        worksheet.merge_range(6, merge_col, 6, col - 1,
                              "Chi tiết giảm / Decreasing Detail", header_bold)
        worksheet.merge_range(6, col, 7, col,
                              "Hình ảnh tài sản / Image of asset", header_bold)
        worksheet.merge_range(6, col + 1, 7, col + 1,
                              "Ghi chú / Remark", header_bold)

        worksheet.merge_range(1, 0, 1, col + 2,
                              title_vi, format.get('title_format'))
        worksheet.merge_range(2, 0, 2, col + 2,
                              title_en, format.get('title_format'))
        start_date = (format_date(self.env, fields.Date.to_string(from_date)))
        end_date = (format_date(self.env, fields.Date.to_string(to_date)))
        worksheet.merge_range(
            3, 0, 3, col + 2,
            f'Từ ngày / From: {start_date} Đến ngày / To: {end_date}', format.get('title_format'))

        row = 8
        plain_format = format.get('plain')
        for asset_id, values in asset_dict.items():
            asset = self.env['account.asset'].browse(asset_id)
            worksheet.write(row, 0, asset.asset_code or '', plain_format)
            worksheet.write(row, 1, asset.name, plain_format)
            worksheet.write(row, 2, asset.asset_quantity, plain_format)
            worksheet.write(row, 3, format_date(
                self.env, fields.Date.to_string(asset.acquisition_date)), plain_format)
            worksheet.write(row, 4, asset.method_number *
                            int(asset.method_period), plain_format)
            col = 5
            for i_reason in increase_reasons:
                worksheet.write(row, col, values.get(
                    i_reason.id, 0), plain_format)
                col += 1
            worksheet.write(row, col, format_date(
                self.env, fields.Date.to_string(asset.asset_purchase_date)), plain_format)
            worksheet.write(
                row, col + 1, asset.asset_supplier_id.name, plain_format)
            col += 2
            for d_reason in decrease_reasons:
                worksheet.write(row, col, values.get(
                    d_reason.id, 0), plain_format)
                col += 1
            if asset.image:
                worksheet.set_row(row, 40)
                image_data = base64.b64decode(asset.image)
                # Save image to a temporary file
                image_path = "temp_image.jpg"
                with open(image_path, "wb") as img_file:
                    img_file.write(image_data)
                worksheet.insert_image(row, col, image_path, {
                                       "x_scale": 0.5, "y_scale": 0.5})
            else:
                worksheet.write(row, col, '', plain_format)
            worksheet.write(row, col + 1, '', plain_format)
            row += 1

        return worksheet

    def _parse_data_allocation_equipment_expenses(self, report_type):
        datas = self._collect_assets_expense_data(report_type)
        title_vi = 'BÁO CÁO PHÂN BỔ CCDC VÀ CHI PHÍ TRẢ TRƯỚC'
        title_en = 'ALLOCATION OF EQUIPMENT AND PREPAID EXPENSES'
        table_titles = [
            ["Mã CCDC / Code", "A7", False],
            ["Tên CCDC / Name", "B7", False],
            ["S.lượng / Qty", "C7", False],
            ["Ngày sử dụng / Start using date", "D7", False],
            ["Số tháng PB / Allocation months", "E7", False],
            ["GT ĐK / Opening balance", "F7", False],
            ["Tăng GT / Increasing", "G7", False],
            ["Giảm GT / Decreasing", "H7", False],
            ["GT CK / Ending balance", "I7", False],
            ["PB ĐK / Accumulated opening balance", "J7", False],
            ["Tăng PB / Increasing", "K7", False],
            ["Giảm PB / Decreasing", "L7", False],
            ["PB CK / Ending balance", "M7", False],
            ["GT còn lại / Remaining value", "N7", False],
            ["TK PB / Allocation acc", "O7", False],
            ["Mã KM / Budget code", "P7", False],
            ["Tên khoản mục / Budget name", "Q7", False]
        ]
        keys = ['asset_code', 'name', 'asset_quantity', 'acquisition_date', 'depreciation_months',
                'opening_original_value', 'increase_original_value', 'decrease_original_value',
                'ending_original_value', 'already_depreciation', 'increase_depreciation', 'decrease_depreciation',
                'ending_depreciation', 'remaining_value', 'account_allocation',
                'budget_code', 'budget_name']
        return title_vi, title_en, table_titles, datas, 17, keys

    def _write_depreciation_fixed_assets_data(self, worksheet, datas, keys, row, plain, bold):
        """Write assets grouped by asset group, with a subtotal row per group."""
        amount_keys = keys[4:13]  # Columns E:M
        grouped_datas = defaultdict(list)
        for data in datas:
            group_key = data['asset_group_id'] or False
            grouped_datas[group_key].append(data)

        for group_datas in grouped_datas.values():
            group_name = group_datas[0]['asset_group_name']
            group_prefix = group_datas[0]['asset_group_prefix']
            worksheet.write(row, 0, group_prefix, bold)
            worksheet.merge_range(row, 1, row, 3, group_name, bold)
            for col, key in enumerate(amount_keys, start=4):
                worksheet.write(
                    row, col,
                    sum(data.get(key) or 0.0 for data in group_datas),
                    bold,
                )
            row += 1

            for data in group_datas:
                for col, key in enumerate(keys):
                    worksheet.write(row, col, data.get(key, ''), plain)
                row += 1
        return row

    def _write_allocation_equipment_expenses_data(self, worksheet, datas, keys, row, plain, bold):
        """Write deferred expenses grouped by their deferred expense model."""
        amount_keys = keys[5:14]  # Columns F:N
        grouped_datas = defaultdict(list)
        for data in datas:
            group_key = data['asset_model_id'] or False
            grouped_datas[group_key].append(data)

        for group_datas in grouped_datas.values():
            worksheet.merge_range(
                row, 0, row, 4, group_datas[0]['asset_model_name'], bold)
            for col, key in enumerate(amount_keys, start=5):
                worksheet.write(
                    row, col,
                    sum(data.get(key) or 0.0 for data in group_datas),
                    bold,
                )
            row += 1

            for data in group_datas:
                for col, key in enumerate(keys):
                    worksheet.write(row, col, data.get(key, ''), plain)
                row += 1
        return row

    def _generate_base64_data(self):
        self.ensure_one()
        filename = dict(self._fields['report'].selection).get(self.report)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(filename)

        title_format = workbook.add_format(
            {'bold': True, 'pattern': 1, 'align': 'center', 'bg_color': '#FFFFFF'})
        header_bold = workbook.add_format(
            {'bold': True, 'pattern': 1, 'bg_color': '#AAAAAA', 'border': 1})
        header_plain = workbook.add_format(
            {'pattern': 1, 'bold': True, 'border': 1, 'bg_color': '#AAAAAA'})
        bold = workbook.add_format(
            {'bold': True, 'border': 1, 'num_format': "#,##0", 'bg_color': '#FFFFFF'})
        plain = workbook.add_format(
            {'pattern': 1, 'border': 1, 'num_format': "#,##0", 'bg_color': '#FFFFFF'})
        row = 7
        # Column width settings
        worksheet.set_column('B:B', 40)
        worksheet.set_column('E:N', 20)

        if self.report == 'fixed_assets_registration':
            worksheet.set_column('D:D', 15)
            worksheet.set_column('M:M', 30)
            self._parse_data_fixed_assets_registration(
                worksheet, {
                    'title_format': title_format,
                    'header_bold': header_bold,
                    'plain': plain
                })
        else:
            if self.report == 'allocation_equipment_expenses':
                worksheet.set_column('D:D', 15)
                worksheet.set_column('O:P', 20)
                worksheet.set_column('Q:Q', 35)
            elif self.report == 'depreciation_fixed_assets':
                worksheet.set_column('C:C', 15)
                worksheet.set_column('O:Q', 20)
                worksheet.set_column('R:R', 35)
                row = 8
            start_date, end_date = self._get_month_start_end()
            # Parse report name
            title_vi, title_en, table_titles, datas, nb_cols, keys = getattr(
                self, f'_parse_data_{self.report}')(self.report)
            worksheet.merge_range(1, 0, 1, nb_cols - 1, title_vi, title_format)
            worksheet.merge_range(2, 0, 2, nb_cols - 1, title_en, title_format)
            start_date = (format_date(
                self.env, fields.Date.to_string(start_date)))
            end_date = (format_date(self.env, fields.Date.to_string(end_date)))
            worksheet.merge_range(
                3, 0, 3, nb_cols - 1,
                f'Từ ngày / From: {start_date} Đến ngày / To: {end_date}', title_format)

            # Parse title of table
            for title_name, cell, merge in table_titles:
                if merge:
                    worksheet.merge_range(cell, title_name, header_bold)
                else:
                    worksheet.write(cell, title_name, header_bold)

            if self.report == 'depreciation_fixed_assets':
                self._write_depreciation_fixed_assets_data(
                    worksheet, datas, keys, row, plain, bold)
            elif self.report == 'allocation_equipment_expenses':
                self._write_allocation_equipment_expenses_data(
                    worksheet, datas, keys, row, plain, bold)
            else:
                for data in datas:
                    col = 0
                    for key in keys:
                        worksheet.write(row, col, data.get(key, ''), plain)
                        col += 1
                    row += 1

        workbook.close()
        xlsx_data = base64.encodebytes(output.getvalue())
        return xlsx_data, f'{filename}.xlsx'

    def action_generate_report(self):
        self.ensure_one()
        binary_data, filename = self._generate_base64_data()
        self.write({
            'binary_file': binary_data,
            'filename': filename
        })
        return {
            'name': _('Assets Report'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
