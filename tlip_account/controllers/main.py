import csv
import io
import json
from collections import deque
import xlsxwriter

from odoo import _, http
from odoo.http import Controller, request, route, content_disposition
from odoo.tools import osutil


class BudgetAnalyticExportController(Controller):

    @http.route('/budget/export/export_xlsx', type='http', auth="user", readonly=True)
    def budget_export_xlsx(self, data, **kw):
        jdata = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(jdata['title'])

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

        measure_count = jdata['measure_count']
        origin_count = jdata['origin_count']

        # Step 1: writing col group headers
        col_group_headers = jdata['col_group_headers'][1:]

        # x,y: current coordinates
        x, y = 4, 7
        for i, header_row in enumerate(col_group_headers):
            h_col = 4
            for header in header_row:
                h_width = header['width']
                worksheet.merge_range(
                    y, h_col, y, h_col + h_width - 1, header['title'], header_plain)
                h_col += h_width
            y += 1
        total_width = h_col
        company = request.env.company
        worksheet.merge_range(
            0, 0, 0, total_width, company.name, title_format)
        addr_format = [
            company.street,
            company.street2,
            company.city,
            company.state_id.name,
            company.country_id.name
        ]
        company_address = ", ".join(
            text for text in addr_format if isinstance(text, str))
        worksheet.merge_range(
            1, 0, 1, total_width, company_address, title_format)
        worksheet.merge_range(
            3, 0, 3, total_width, jdata['title'], title_format)
        open_year = request.env['budget.analytic.year'].search([
            ('state', '=', 'confirmed')], limit=1)
        if open_year:
            worksheet.merge_range(
                4, 0, 4, total_width, f'From {open_year.fiscal_year_id.date_from} To {open_year.fiscal_year_id.date_to}', title_format)

        # Step 2: writing measure headers
        measure_headers = jdata['measure_headers']

        if measure_headers:
            for measure in measure_headers:
                style = header_bold if measure['is_bold'] else header_plain
                worksheet.write(y, x, measure['title'], style)
                for i in range(1, 2 * origin_count - 1):
                    worksheet.write(y, x + i, '', header_plain)
                x = x + (2 * origin_count - 1)
            x, y = 1, y + 1
            # set minimum width of cells to 16 which is around 88px
            worksheet.set_column(0, len(measure_headers) + 4, 16)

        # Step 3: writing origin headers
        origin_headers = jdata['origin_headers']

        if origin_headers:
            worksheet.write(y, 0, '', header_plain)
            for origin in origin_headers:
                style = header_bold if origin['is_bold'] else header_plain
                worksheet.write(y, x, origin['title'], style)
                x = x + 1
            y = y + 1

        # Step 4: writing data
        worksheet.merge_range(7, 0, 8, 0, 'Budget Code', header_plain)
        worksheet.merge_range(7, 1, 8, 1, 'Dept. Code', header_plain)
        worksheet.merge_range(7, 2, 8, 2, 'Full Code', header_plain)
        worksheet.merge_range(7, 3, 8, 3, 'Budget Name', header_plain)
        rows = jdata['rows'][1:]
        for row in rows:
            code, dept_code, full_code, budget_name = row['title'], '', '', ''
            category = request.env['budget.category'].search(
                [('code', '=', code)])
            row_format = plain
            if category:
                code = category.code
                budget_name = category.name
                row_format = bold
            else:
                budget = request.env['account.analytic.account'].search(
                    [('complete_code', '=', code)], limit=1)
                if budget:
                    dept_code = budget.budget_department_id.code
                    full_code = f'{dept_code}-{code}'
                    budget_name = budget.name
            worksheet.write(y, 0, code, row_format)
            worksheet.write(y, 1, dept_code, plain)
            worksheet.write(y, 2, full_code, plain)
            worksheet.write(y, 3, budget_name, row_format)
            x = 4
            for cell in row['values']:
                value = cell['value'] or 0
                if cell.get('is_bold', False):
                    worksheet.write(y, x, value, bold)
                else:
                    worksheet.write(y, x, value, plain)
                x += 1
            y += 1

        workbook.close()
        xlsx_data = output.getvalue()
        filename = osutil.clean_filename(
            _("%(title)s", title=jdata['title']))
        response = request.make_response(xlsx_data,
                                         headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                                                  ('Content-Disposition', content_disposition(filename + '.xlsx'))],
                                         )

        return response
