# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import io
import math
import datetime
import markupsafe
from odoo import models, fields, _
from odoo.tools import config, get_lang
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import xlsxwriter, DEFAULT_SERVER_DATE_FORMAT


class TrialBalanceCustomHandler(models.AbstractModel):
    _inherit = 'account.trial.balance.report.handler'

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        options["buttons"].extend([
            {"name": _("S06-DN(XLSX)"), 'sequence': 110, 'action': 'export_file', 'action_param': 'export_to_s06_dn_xlsx', 'file_export_type': _('XLSX')},
            {"name": _("S06-DN(PDF)"), 'sequence': 120, 'action': 'export_file', 'action_param': 'export_to_s06_dn_pdf', 'file_export_type': _('PDF')}
        ])

    def _custom_line_postprocessor(self, report, options, lines):
        lines_result = super(TrialBalanceCustomHandler, self)._custom_line_postprocessor(report, options, lines)
        if options.get('hierarchy'):
            for line in lines:
                model, dummy = report._get_model_info_from_id(line['id'])
                if model == 'account.group' and dummy:
                    account_group_id = self.env[model].browse(int(dummy))
                    if account_group_id:
                        if account_group_id.name and account_group_id.code:
                            line["name"] = f"{account_group_id.code}-{account_group_id.name}"
                        elif account_group_id.name and not account_group_id.code:
                            line["name"] = f"{account_group_id.name}"
                        line["account_group_id_code"] = account_group_id.code or ""
                        line["account_group_id_name"] = account_group_id.name or ""
                elif model == "account.account" and dummy:
                    account_account_id = self.env[model].browse(int(dummy))
                    if account_account_id:
                        line["account_code"] = account_account_id.code or ""
                        line["account_name"] = account_account_id.name or ""
        elif options.get('hierarchy') is False:
            for line in lines:
                model, dummy = report._get_model_info_from_id(line['id'])
                if model == "account.account" and dummy:
                    account_account_id = self.env[model].browse(int(dummy))
                    if account_account_id:
                        line["account_code"] = account_account_id.code or ""
                        line["account_name"] = account_account_id.name or ""
        return lines_result


class AccountReport(models.Model):
    _inherit = 'account.report'

    def get_s06_dn_default_report_filename(self, extension):
        """The default to be used for the file when downloading pdf,xlsx,..."""
        self.ensure_one()
        return f"Bảng cân đối số phát sinh.{extension}"

    def _get_current_quarter_number(self, today=None):
        if today == 1 or today == 2 or today == 3:
            quarter_number = 1
        elif today == 4 or today == 5 or today == 6:
            quarter_number = 2
        elif today == 7 or today == 8 or today == 9:
            quarter_number = 3
        elif today == 10 or today == 11 or today == 12:
            quarter_number = 4
        return quarter_number

    def _get_s06_dn_format_float_number(self, number):
        number_format = ''
        if number:
            if number % 1 == 0:
                number_format = "{:,.0f}".format(number)
            else:
                number_format = "{:,.2f}".format(number).rstrip('0')
        return number_format

    def _get_s06_dn_date_now(self):
        date_now = fields.Date.today()
        return f"Ngày {date_now.day} tháng {date_now.month} năm {date_now.year}"

    def _get_s06_dn_format_date(self, options):
        date = options.get("date")
        year = datetime.datetime.today().year
        if date.get("filter") == "this_month":
            month = datetime.datetime.today().month
            return _("Tháng %s năm %s", str(month), str(year))
        elif date.get("filter") == "last_month":
            month = (datetime.datetime.today() - relativedelta(months=1)).month
            year = (datetime.datetime.today() - relativedelta(months=1)).year
            return _("Tháng %s năm %s", str(month), str(year))
        elif date.get("filter") == "this_quarter":
            quarter = math.ceil(datetime.datetime.today().month/3.)
            return _("Quý %s năm %s", str(quarter), str(year))
        elif date.get("filter") == "last_quarter":
            month = (datetime.datetime.today() - relativedelta(months=3)).month
            quarter = self._get_current_quarter_number(today=month)
            year = (datetime.datetime.today() - relativedelta(months=3)).year
            return _("Quý %s năm %s", str(quarter), str(year))
        elif date.get("filter") == "this_year":
            return _("Năm %s", str(year))
        elif date.get("filter") == "last_year":
            year = (datetime.datetime.today() - relativedelta(years=1)).year
            return _("Năm %s", str(year))
        else:
            date_from = datetime.datetime.strptime(date.get("date_from"),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') if date.get("date_from") else ""
            date_to = datetime.datetime.strptime(date.get("date_to"), DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') if date.get("date_to") else ""
            return _("%s đến %s", date_from, date_to)

    def _get_s06_dn_company_name(self, company_ids):
        if not company_ids:
            return ""
        company_ids = self.env["res.company"].browse(company_ids)
        return ",".join([company.name for company in company_ids if company.name != False])

    def _get_s06_dn_company_address(self, company):
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

    def _get_s06_dn_company_street(self, company_ids):
        if not company_ids:
            return ""
        company_ids = self.env["res.company"].browse(company_ids)
        return ",".join([self._get_s06_dn_company_address(company) for company in company_ids])

    def _get_s06_dn_cell_value(self, cell):
        if cell.get("account_group_id_code") or cell.get("account_group_id_name"):
            return ('text', cell.get("account_group_id_code", ""), cell.get("account_group_id_name", ""), True)
        elif cell.get("account_code") or cell.get("account_name"):
            return ("text", cell.get("account_code", ""), cell.get("account_name", ""), False)
        elif cell.get("class") == "total":
            cell["name"] = "Tổng cộng"
            return ('text', cell.get('name', ''), cell.get('name', ''), False)
        return ('text', cell.get('name', ''), cell.get('name', ''), False)

    def export_to_s06_dn_xlsx(self, options, response=None):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        sheet = workbook.add_worksheet(self.name[:31])

        # Style
        # border_left = workbook.add_format({'font_name': 'Arial', 'align': 'left', 'border': 1, 'text_wrap': True})
        bold_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'left'})
        bold_center = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center'})
        border_center = workbook.add_format({'font_name': 'Arial', 'align': 'center', 'border': 1})
        bold_title_center = workbook.add_format({'font_name': 'Arial', 'font_size': 15, 'bold': True, 'align': 'center'})
        center = workbook.add_format({'font_name': 'Arial', 'align': 'center'})
        italic_center = workbook.add_format({'font_name': 'Arial', 'align': 'center', 'italic': 1})
        border_bold_center = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'center', 'border': 1})
        border_bold_center.set_text_wrap()

        border_left_bold = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'right', 'border': 1})
        border_left_right = workbook.add_format({'font_name': 'Arial', 'left': 1, 'right': 1, 'align': 'right'})
        border_left_right_bold = workbook.add_format({'font_name': 'Arial', 'bold': True, 'left': 1, 'right': 1, 'align': 'right'})

        border_left_bold_align_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'align': 'left', 'border': 1, 'valign': 'vcenter'})
        border_left_bold_align_left.set_text_wrap()
        border_left_right_align_left = workbook.add_format({'font_name': 'Arial', 'left': 1, 'right': 1, 'valign': 'vcenter'})
        border_left_right_align_left.set_text_wrap()
        border_left_right_bold_align_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'left': 1, 'right': 1, 'valign': 'vcenter'})
        border_left_right_bold_align_left.set_text_wrap()

        sheet.hide_gridlines(2)

        y_offset = 11
        y_offset_custom = y_offset
        print_mode_self = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)
        print_options = print_mode_self.get_options(previous_options=options)
        lines = self._filter_out_folded_children(print_mode_self._get_lines(print_options))

        if print_options.get('order_column'):
            lines = self._sort_lines(lines, print_options)

        # set_column(first_col, last_col, width, cell_format, options)
        sheet.set_column(0, 0, 18)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 7, 22)

        for y in range(0, len(lines)):
            level = lines[y].get('level')
            cell_type, cell_value_code, cell_value_name, is_hierarchy = self._get_s06_dn_cell_value(lines[y])
            if lines[y].get('caret_options'):
                style = border_left_right
                col1_style = border_left_right_align_left
            elif level == 1 or is_hierarchy:
                if lines[y].get("class") != "total":
                    style = border_left_right_bold
                    col1_style = border_left_right_bold_align_left
                else:
                    style = border_left_bold
                    col1_style = border_left_bold_align_left
            elif level == 2:
                style = border_left_right
                col1_style = border_left_bold_align_left
            else:
                style = border_left_right
                col1_style = border_left_bold_align_left

            if cell_type == "text":
                if lines[y].get("class") == "total":
                    sheet.write(y + y_offset, 0, "", col1_style)
                else:
                    sheet.write(y + y_offset, 0, cell_value_code, col1_style)
                sheet.write(y + y_offset, 1, cell_value_name, col1_style)

            columns = lines[y]['columns']
            for x, column in enumerate(columns, start=2):
                cell_type, cell_value = self._get_cell_type_value(column)
                sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, self._get_s06_dn_format_float_number(cell_value), style)

            y_offset_custom += 1

        # merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, 0, 0, 4, "Đơn vị: " + self._get_s06_dn_company_name(self.get_report_company_ids(options)), bold_left)
        sheet.merge_range(1, 0, 1, 4, "Địa chỉ: " + self._get_s06_dn_company_street(self.get_report_company_ids(options)), bold_left)
        sheet.merge_range(0, 5, 0, 7, "Mẫu số S06-DN", bold_center)
        sheet.merge_range(1, 5, 1, 7, "(Ban hành theo Thông tư số 200/2014/TT-BTC", center)
        sheet.merge_range(2, 5, 2, 7, "Ngày 22/12/2014 của Bộ Tài chính)", center)
        sheet.merge_range(3, 1, 3, 5, "Bảng cân đối số phát sinh", bold_title_center)
        sheet.merge_range(4, 1, 4, 5, self._get_s06_dn_format_date(options), center)
        sheet.merge_range(8, 0, 9, 0, "Số hiệu tài khoản", border_bold_center)
        sheet.merge_range(8, 1, 9, 1, "Tên tài khoản kế toán", border_bold_center)
        sheet.merge_range(8, 2, 8, 3, "Số dư đầu tháng", border_bold_center)
        sheet.merge_range(8, 4, 8, 5, "Số phát sinh trong tháng", border_bold_center)
        sheet.merge_range(8, 6, 8, 7, "Số dư cuối tháng", border_bold_center)



        # write(row, col, data, format)
        sheet.write(10, 0, "A", border_center)
        sheet.write(10, 1, "B", border_center)
        sheet.write(9, 2, "Nợ", border_center)
        sheet.write(9, 3, "Có", border_center)
        sheet.write(9, 4, "Nợ", border_center)
        sheet.write(9, 5, "Có", border_center)
        sheet.write(9, 6, "Nợ", border_center)
        sheet.write(9, 7, "Có", border_center)
        sheet.write(10, 2, "1", border_center)
        sheet.write(10, 3, "2", border_center)
        sheet.write(10, 4, "3", border_center)
        sheet.write(10, 5, "4", border_center)
        sheet.write(10, 6, "5", border_center)
        sheet.write(10, 7, "6", border_center)

        # merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        y_offset_custom += 2
        sheet.merge_range(y_offset_custom, 6, y_offset_custom, 7, self._get_s06_dn_date_now(), italic_center)
        y_offset_custom += 1
        sheet.merge_range(y_offset_custom, 0, y_offset_custom, 1, "Người ghi sổ", bold_center)
        sheet.merge_range(y_offset_custom, 2, y_offset_custom, 3, "Kế toán trưởng", bold_center)
        sheet.merge_range(y_offset_custom, 6, y_offset_custom, 7, "Giám đốc", bold_center)
        y_offset_custom += 1
        sheet.merge_range(y_offset_custom, 0, y_offset_custom, 1, "(Ký, họ tên)", italic_center)
        sheet.merge_range(y_offset_custom, 2, y_offset_custom, 3, "(Ký, họ tên)", italic_center)
        sheet.merge_range(y_offset_custom, 6, y_offset_custom, 7, "(Ký, họ tên, đóng dấu)", italic_center)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()
        return {
            'file_name': self.get_s06_dn_default_report_filename('xlsx'),
            'file_content': generated_file,
            'file_type': 'xlsx',
        }

    def export_to_s06_dn_pdf(self, options):
        self.ensure_one()
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
        }

        print_mode_self = self.with_context(print_mode=True)
        print_options = print_mode_self.get_options(previous_options=options)
        body_html = print_mode_self._get_pdf_export_html(
            options=print_options,
            lines=print_mode_self._filter_out_folded_children(print_mode_self._get_lines(print_options)),
            additional_context={
                "template": 'biz_balance_sheet_according_to_circular_no_200.s06_dn_pdf',
                "report_s06_dn_company_street": self._get_s06_dn_company_street(self.get_report_company_ids(options)),
                "report_s06_dn_date": self._get_s06_dn_format_date(options),
                "report_so6_dn_date_now": self._get_s06_dn_date_now()
            }
        )
        footer = self.env['ir.actions.report']._render_template("biz_balance_sheet_according_to_circular_no_200.custom_internal_layout", values=rcontext)
        footer = self.env['ir.actions.report']._render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=markupsafe.Markup(footer.decode())))

        landscape = False
        if len(print_options['columns']) * len(print_options['column_groups']) > 5:
            landscape = True

        file_content = self.env['ir.actions.report']._run_wkhtmltopdf(
            [body_html],
            footer=footer.decode(),
            landscape=landscape,
            specific_paperformat_args={
                'data-report-margin-top': 10,
                'data-report-header-spacing': 10,
                'data-report-margin-bottom': 15,
            }
        )

        return {
            'file_name': self.get_s06_dn_default_report_filename('pdf'),
            'file_content': file_content,
            'file_type': 'pdf',
        }
    
    def _format_lines_for_display(self, lines, options):
        lines = super(AccountReport, self)._format_lines_for_display(lines=lines, options=options)
        if self._context.get("is_s06_dn_pdf"):
            for line in lines:
                if line.get("account_group_id_code") or line.get("account_group_id_name"):
                    for column in line.get("columns"):
                        if column.get("no_format") != 0:
                            column["name"] = column["name"].replace(" ₫", "").replace(".", ",")
                            column["style"] = "font-weight: bold; text-align: right;"
                        elif column.get("no_format") == 0 and not column.get("name"):
                            column["name"] = "0"
                            column["style"] = "font-weight: bold; text-align: right;"
                elif line.get("account_code") or line.get("account_name"):
                    for column in line.get("columns"):
                        if column.get("no_format") != 0:
                            column["name"] = column["name"].replace(" ₫", "").replace(".", ",")
                        elif column.get("no_format") == 0 and not column.get("name"):
                            column["name"] = "0"
                elif line.get("class") == " o_account_coa_column_contrast_hierarchy":
                    for column in line.get("columns"):
                        if column.get("no_format") != 0:
                            column["name"] = column["name"].replace(" ₫", "").replace(".", ",")
                            column["style"] = "font-weight: bold; text-align: right;"
                        elif column.get("no_format") == 0 and not column.get("name"):
                            column["name"] = "0"
                            column["style"] = "font-weight: bold; text-align: right;"
                elif line.get("class") == "total":
                    if line.get("name"):
                        line["name"] = "Tổng cộng"
                    for column in line.get("columns"):
                        if column.get("no_format") != 0:
                            column["name"] = column["name"].replace(" ₫", "").replace(".", ",")
                            column["style"] = "font-weight: bold; text-align: right;"
                            column["class"] = ""
                        elif column.get("no_format") == 0:
                            column["name"] = "0"
                            column["style"] = "font-weight: bold; text-align: right;"
                            column["class"] = ""
        return lines
