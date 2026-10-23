# -*- coding: utf-8 -*-


from odoo import fields, models, _
from odoo.tools.misc import xlsxwriter
from odoo.models import check_method_name
from odoo.exceptions import UserError

import json
import io
import datetime
import markupsafe


class AccountPublicDiaryWizard(models.Model):
    _name = "account.public.diary.wizard"
    _description = "Public Diary"

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    def _get_s03a_dn_company_name(self):
        company_ids = self.env["res.company"].browse(self.env.company.ids)
        return ",".join([company.name for company in company_ids if company.name != False])

    def _get_s03a_dn_company_address(self, company):
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

    def _get_s03a_dn_company_street(self):
        company_ids = self.env["res.company"].browse(self.env.company.ids)
        return ",".join([self._get_s03a_dn_company_address(company) for company in company_ids if company.street != False])

    def _get_s03a_dn_format_float_number(self, number):
        number_format = ''
        if number:
            if number % 1 == 0:
                number_format = "{:,.0f}".format(number)
            else:
                number_format = "{:,.2f}".format(number).rstrip('0')
        return number_format

    def _get_s03a_dn_filter_date(self, options):
        date = options.get("date")
        date_from = datetime.datetime.strptime(date.get("date_from"), "%d/%m/%Y")
        date_to = datetime.datetime.strptime(date.get("date_to"), "%d/%m/%Y")
        if date_from.month == date_to.month and date_from.year == date_to.year:
            return _("Tháng %s Năm %s", str(date_from.month), str(date_from.year))
        elif date_from.month == date_to.month and date_from.year != date_to.year:
            return _("Năm %s", str(date_from.year))
        else:
            return _("Từ ngày: %s đến ngày: %s", date.get("date_from"), date.get("date_to"))

    def _get_s03a_dn_format_date(self, date):
        if not date:
            return ''
        return date.strftime('%d/%m/%Y')

    def _get_s03a_dn_lines(self, options):
        lines = []
        lines_custom = []
        columns = []
        date = options.get("date")
        date_from = datetime.datetime.strptime(date.get("date_from"), "%d/%m/%Y")
        date_to = datetime.datetime.strptime(date.get("date_to"), "%d/%m/%Y")
        account_move = self.env["account.move"]

        domain = [
            ("date", "<", date_from),
            ("state", "=", "posted"),
            ("company_id", "=", self.env.company.id)
        ]
        account_move_count = account_move.search_count(domain)
        if account_move_count:
            account_move_search = account_move.search(domain)
            lines_custom.append({
                "name": "total",
                "columns": [
                    {
                        "class": "number",
                        "title": "debit",
                        "name": sum(account_move_search.line_ids.mapped("debit")),
                    },
                    {
                        "class": "number",
                        "title": "credit",
                        "name": sum(account_move_search.line_ids.mapped("credit")),
                    }
                ],
            })

        domain = [
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("state", "=", "posted"),
            ("company_id", "=", self.env.company.id)
        ]
        account_move_count = account_move.search_count(domain)
        if account_move_count:
            account_move_search = account_move.search(domain, order="date asc")

            def _get_columns(line_ids):
                vals_list = []
                stt = 1
                for line in line_ids:
                    vals_list.append({
                        "stt": stt,
                        "name": line.account_id.code or '',
                        "diengiai": line.name or '',
                        "debit": line.debit or 0,
                        "credit": line.credit or 0
                    })
                    stt += 1
                return vals_list
            for account in sorted(account_move_search,key= lambda x:(x.date,x.name)):
                columns = _get_columns(account.line_ids)
                lines.append({
                    "name": account.name or '',
                    "ref": account.ref or (columns and columns[0].get('diengiai') or ''),
                    "date": account.date or '',
                    "columns": columns,
                })
            else:
                debit = 0
                credit = 0
                for line in lines:
                    for child_line in line.get("columns"):
                        debit += child_line["debit"]
                        credit += child_line["credit"]

                lines.append({
                    "name": "total",
                    "columns": [{
                        "name": "total",
                        "debit": debit,
                        "credit": credit,
                    }]
                })
        return lines, lines_custom

    def export_to_s03a_dn_pdf(self, options):
        self.ensure_one()
        print_mode_self = self.with_context(print_mode=True)
        body_html = print_mode_self.get_html(options=options, template="biz_account_public_diary.s03a_dn_pdf")
        file_content = self.env['ir.actions.report']._run_wkhtmltopdf(
            [body_html],
            footer=False,
            landscape=True,
            specific_paperformat_args={
                'data-report-margin-top': 10,
                'data-report-header-spacing': 10,
                'data-report-margin-bottom': 15,
            }
        )

        return {
            'file_name': self.get_default_report_filename(options, 'pdf'),
            'file_content': file_content,
            'file_type': 'pdf',
        }

    def export_to_s03a_dn_xlsx(self, options):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        sheet = workbook.add_worksheet("Sổ nhật ký chung")

        # Style
        border_left = workbook.add_format({'font_name': 'Times New Roman', 'align': 'left', 'border': 1, 'text_wrap': True, 'valign': 'vcenter'})
        border_right = workbook.add_format({'font_name': 'Times New Roman', 'align': 'right', 'border': 1, 'text_wrap': True, 'valign': 'vcenter'})
        bold_left = workbook.add_format({'font_name': 'Times New Roman', 'bold': True, 'align': 'left', 'text_wrap': True, 'valign': 'vcenter'})
        bold_center = workbook.add_format({'font_name': 'Times New Roman', 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        bold_title_center_header = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        bold_title_center = workbook.add_format({'font_name': 'Times New Roman', 'font_size': 15, 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        center = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'valign': 'vcenter'})
        border_center = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'border': 1, 'valign': 'vcenter'})
        left = workbook.add_format({'font_name': 'Times New Roman', 'align': 'left', 'valign': 'vcenter'})
        italic_center = workbook.add_format({'font_name': 'Times New Roman', 'align': 'center', 'italic': 1, 'valign': 'vcenter'})
        border_bold_center = workbook.add_format({'font_name': 'Times New Roman', 'bold': True, 'align': 'center', 'border': 1, 'valign': 'vcenter'})
        border_bold_center.set_text_wrap()
        border_bold_left = workbook.add_format({'font_name': 'Times New Roman', 'bold': True, 'align': 'left', 'border': 1, 'valign': 'vcenter'})
        border_bold_right = workbook.add_format({'font_name': 'Times New Roman', 'bold': True, 'align': 'right', 'border': 1, 'valign': 'vcenter'})

        x_offset = 12
        y_offset = y_offset_custom = 11
        stt = 1
        lines, lines_custom = self._get_s03a_dn_lines(options)

        # set_column(first_col, last_col, width, cell_format, options)
        sheet.set_column(0, 2, 20)
        sheet.set_column(3, 3, 32)
        sheet.set_column(4, 8, 20)

        # set_row(row, height, cell_format, options)
        sheet.set_row(0, 23)
        sheet.set_row(1, 30)
        sheet.set_row(3, 20)

        for y in range(0, len(lines_custom)):
            sheet.write(y + y_offset, 0, "", border_bold_left)
            sheet.write(y + y_offset, 1, "", border_bold_left)
            sheet.write(y + y_offset, 2, "", border_bold_left)
            sheet.write(y + y_offset, 3, "Số trang trước chuyển sang", border_bold_left)
            sheet.write(y + y_offset, 4, "", border_bold_left)
            sheet.write(y + y_offset, 5, "", border_bold_left)
            sheet.write(y + y_offset, 6, "", border_bold_left)
            columns = lines_custom[y]['columns']
            for x, column in enumerate(columns, start=7):
                cell_type, cell_value = self.env["account.report"]._get_cell_type_value(column)
                sheet.write(y + y_offset, x + 1 - 1, self._get_s03a_dn_format_float_number(cell_value), border_bold_right)

            y_offset_custom += 1

        if not lines_custom:
            sheet.write(y_offset, 0, "", border_bold_left)
            sheet.write(y_offset, 1, "", border_bold_left)
            sheet.write(y_offset, 2, "", border_bold_left)
            sheet.write(y_offset, 3, "Số trang trước chuyển sang", border_bold_left)
            sheet.write(y_offset, 4, "", border_bold_left)
            sheet.write(y_offset, 5, "", border_bold_left)
            sheet.write(y_offset, 6, "", border_bold_left)
            sheet.write(y_offset, 7, "0", border_bold_left)
            sheet.write(y_offset, 8, "0", border_bold_left)
            y_offset_custom += 1

        for y in range(0, len(lines)):
            sheet.write(y_offset_custom, 0, self._get_s03a_dn_format_date(lines[y].get("date")), border_left)
            sheet.write(y_offset_custom, 1, lines[y].get("name"), border_left)
            sheet.write(y_offset_custom, 2, self._get_s03a_dn_format_date(lines[y].get("date")), border_left)
            sheet.write(y_offset_custom, 3, lines[y].get("ref"), border_left)
            if lines[y].get("name") == "total":
                sheet.write(y_offset_custom, 1, "", border_left)
                sheet.write(y_offset_custom, 3, "Cộng chuyển sang trang sau", border_bold_left)
            columns = lines[y]['columns']
            for column in columns:
                start = 4
                if column.get("name") == "total":
                    sheet.write(x_offset, start, "x", border_center)
                    sheet.write(x_offset, start + 1, "x", border_center)
                    sheet.write(x_offset, start + 2, "x", border_center)
                else:
                    sheet.write(x_offset, start, "x", border_center)
                    sheet.write(x_offset, start + 1, str(stt), border_center)
                    sheet.write(x_offset, start + 2, column.get("name"), border_left)
                    stt += 1

                if column.get("debit") > 0:
                    sheet.write(x_offset, start + 3, self._get_s03a_dn_format_float_number(column.get("debit")), border_right)
                else:
                    sheet.write(x_offset, start + 3, "0", border_right)
                if column.get("credit") > 0:
                    sheet.write(x_offset, start + 4, self._get_s03a_dn_format_float_number(column.get("credit")), border_right)
                else:
                    sheet.write(x_offset, start + 4, "0", border_right)
                if column.get("stt") and column.get("stt") > 1:
                    sheet.write(x_offset, 0, "", border_left)
                    sheet.write(x_offset, 1, "", border_left)
                    sheet.write(x_offset, 2, "", border_left)
                    sheet.write(x_offset, 3, column.get("diengiai"), border_left)
                x_offset += 1
            y_offset_custom += 1 if not columns else len(columns)

        # merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, 0, 0, 5, "Đơn vị: " + self._get_s03a_dn_company_name(), bold_left)
        sheet.merge_range(1, 0, 1, 5, "Địa chỉ: " + self._get_s03a_dn_company_street(), bold_left)
        sheet.merge_range(0, 6, 0, 8, "Mẫu số S03a-DN", bold_title_center_header)
        sheet.merge_range(1, 6, 1, 8, "(Ban hành theo Thông tư số 200/2014/TT-BTC", italic_center)
        sheet.merge_range(2, 6, 2, 8, "Ngày 22/12/2014 của Bộ Tài chính)", italic_center)
        sheet.merge_range(3, 2, 3, 6, "SỔ NHẬT KÝ CHUNG", bold_title_center)
        sheet.merge_range(4, 2, 4, 6, self._get_s03a_dn_filter_date(options), center)
        sheet.merge_range(7, 7, 7, 8, "Đơn vị tính: Đồng", italic_center)
        sheet.merge_range(8, 0, 9, 0, "Ngày, tháng ghi sổ", border_bold_center)
        sheet.merge_range(8, 1, 8, 2, "Chứng từ", border_bold_center)
        sheet.merge_range(8, 3, 9, 3, "Diễn giải", border_bold_center)
        sheet.merge_range(8, 4, 9, 4, "Đã ghi sổ cái", border_bold_center)
        sheet.merge_range(8, 5, 9, 5, "STT dòng", border_bold_center)
        sheet.merge_range(8, 6, 9, 6, "Số hiệu TK đối ứng", border_bold_center)
        sheet.merge_range(8, 7, 8, 8, "Số phát sinh", border_bold_center)

        # write(row, col, data, format)
        sheet.write(9, 1, "Số hiệu", border_bold_center)
        sheet.write(9, 2, "Ngày, tháng", border_bold_center)
        sheet.write(9, 7, "Nợ", border_bold_center)
        sheet.write(9, 8, "Có", border_bold_center)
        sheet.write(10, 0, "A", border_bold_center)
        sheet.write(10, 1, "B", border_bold_center)
        sheet.write(10, 2, "C", border_bold_center)
        sheet.write(10, 3, "D", border_bold_center)
        sheet.write(10, 4, "E", border_bold_center)
        sheet.write(10, 5, "G", border_bold_center)
        sheet.write(10, 6, "H", border_bold_center)
        sheet.write(10, 7, "1", border_bold_center)
        sheet.write(10, 8, "2", border_bold_center)

        # merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(y_offset_custom, 0, y_offset_custom, 3, "- Sổ này có ..... trang, đánh số từ trang số 01 đến trang .....", left)
        y_offset_custom += 1
        sheet.merge_range(y_offset_custom, 0, y_offset_custom, 3, "- Ngày mở sổ: ...", left)
        y_offset_custom += 1
        sheet.merge_range(y_offset_custom, 6, y_offset_custom, 8, "Ngày...tháng...năm...", italic_center)
        y_offset_custom += 1
        sheet.merge_range(y_offset_custom, 0, y_offset_custom, 1, "Người lập biểu", bold_center)
        sheet.merge_range(y_offset_custom, 3, y_offset_custom, 4, "Kế toán trưởng", bold_center)
        sheet.merge_range(y_offset_custom, 6, y_offset_custom, 8, "Người đại diện theo pháp luật", bold_center)
        y_offset_custom += 1
        sheet.merge_range(y_offset_custom, 0, y_offset_custom, 1, "(Ký, họ tên)", center)
        sheet.merge_range(y_offset_custom, 3, y_offset_custom, 4, "(Ký, họ tên)", center)
        sheet.merge_range(y_offset_custom, 6, y_offset_custom, 8, "(Ký, họ tên, đóng dấu)", center)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return {
            'file_name': self.get_default_report_filename(options, 'xlsx'),
            'file_content': generated_file,
            'file_type': 'xlsx',
        }

    def export_file(self):
        self.ensure_one()
        file_generator = self._context.get("file_generator")
        if self.from_date > self.to_date:
            raise UserError(_("Đến ngày không được nhỏ hơn từ ngày."))
        options = {
            "report_id": self.id,
            "date": {
                "date_from": self.from_date.strftime('%d/%m/%Y'),
                "date_to": self.to_date.strftime('%d/%m/%Y'),
            }
        }
        return {
            'type': 'ir_actions_account_public_diary',
            'data': {
                'options': json.dumps(options),
                'file_generator': file_generator,
            }
        }

    def get_html(self, options, template=None):
        render_values = {
            'report': self,
            'report_company_name': self.env.company.name,
            'report_s03a_dn_company_street': self._get_s03a_dn_company_street(),
            'report_s03a_dn_date': self._get_s03a_dn_filter_date(options),
            'lines': self._get_s03a_dn_lines(options),
            'model': self,
            'table_start': markupsafe.Markup('<tbody>'),
            'table_end': markupsafe.Markup('''
                </tbody></table>
                <div style="page-break-after: always"></div>
                <table class="o_account_reports_table table-hover s03a-dn-table">
            '''),
        }
        # Render.
        html = self.env['ir.qweb']._render(template, render_values)
        return html

    def get_default_report_filename(self, options, extension):
        """The default to be used for the file when downloading pdf,xlsx,..."""
        self.ensure_one()
        date = options.get("date")
        date_from = date.get("date_from", '')
        date_to = date.get("date_to", '')
        return f"Sổ nhật ký chung {date_from}-{date_to}.{extension}"

    def dispatch_report_action(self, options, action, action_param=None):
        """ Dispatches calls made by the client to either the report itself, or its custom handler if it exists.
            The action should be a public method, by definition, but a check is made to make sure
            it is not trying to call a private method.
        """
        self.ensure_one()
        check_method_name(action)
        args = [options, action_param] if action_param is not None else [options]
        return getattr(self, action)(*args)
