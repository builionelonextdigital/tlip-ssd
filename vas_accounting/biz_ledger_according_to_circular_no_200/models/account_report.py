from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date, xlsxwriter
import io
import logging
from odoo.exceptions import ValidationError
from collections import defaultdict
from datetime import datetime,timedelta
_logger = logging.getLogger(__name__)
from babel.dates import get_quarter_names
from odoo.tools import config, date_utils, get_lang, float_compare, float_is_zero
import markupsafe

cols = {
    'column0':0,
    'column1':1,
    'column2':2,
    'column3':3,
    'column4':4,
    'column5':5,
    'column6':6,
    'column7':7,
    'column8':8,
}


class AccountReport(models.Model):
    _inherit = 'account.report'


    def _init_options_buttons(self, options, previous_options=None):
        super(AccountReport, self)._init_options_buttons(options, previous_options=previous_options)
        general_ledger = self.env.ref('account_reports.general_ledger_report')
        if self and general_ledger and self == general_ledger:
            options['buttons'] = [
                {'name': _('PDF'), 'sequence': 10, 'action': 'export_file', 'action_param': 'export_to_pdf', 'file_export_type': _('PDF')},
                {'name': _('XLSX'), 'sequence': 20, 'action': 'export_file', 'action_param': 'export_to_xlsx', 'file_export_type': _('XLSX')},
                {'name': _('Save'), 'sequence': 100, 'action': 'open_report_export_wizard'},
                {'name': _('S03b-DN (XLSX)'), 'sequence': 110, 'action': 'export_file', 'action_param': 'export_general_ledger_xlsx', 'file_export_type': _('XLSX')},
                {'name': _('S03b-DN (PDF)'), 'sequence': 120, 'action': 'export_file', 'action_param': 'export_to_pdf_custom', 'file_export_type': _('PDF')},
            ]

    def export_to_pdf_custom(self, options):
        self.ensure_one()
        if not options.get('account_ids'):
            raise ValidationError('Vui lòng chọn tài khoản')
        options['unfold_all'] = True
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.company,
        }
        #value in template
        report = self.env.ref('account_reports.general_ledger_report')
        account = options.get('account_ids',[])
        account_ids = self.env['account.account'].sudo().search([('id','in',account)])
        account_name = 'Tên tài khoản: %s' %(self.mapped_account(account_ids,value='name'))
        account_code = 'Số hiệu: %s' %(self.mapped_account(account_ids,value='code'))

        array_acc = []
        for acc in account_ids:
            array_acc.append(report._get_generic_line_id('account.account', acc.id))

        array_line = []

        for arr in array_acc:
            total_debit = 0
            total_credit = 0

            model, model_id = report._get_model_info_from_id(arr)
            account, init_balance_by_col_group = self.env['account.general.ledger.report.handler']._get_initial_balance_values(report, [model_id], options)[model_id]

            value = list(init_balance_by_col_group.values())[0]
            aml_results = self.env['account.general.ledger.report.handler']._get_aml_values(report, options, [model_id])
            aml_results = list(aml_results)[0][model_id] if aml_results else []
            sum_sodu_no = value.get('balance') if value.get('balance') and value.get('balance') > 0 else 0
            sum_sodu_co = value.get('balance') if value.get('balance') and value.get('balance') < 0 else 0
            line_show = self.get_lines_xlsx(aml_results)
            for line in line_show:
                for key, val in line.items():
                    line[key] = [val,False]
                    if key == 'column7':
                        total_debit += val if val else 0
                        line[key] = ['{:,}'.format(int(val)) if val else 0,'right']
                    if key == 'column8':
                        total_credit += val if val else 0
                        line[key] = ['{:,}'.format(int(val)) if val else 0,'right']

            total_array = []
            value_calculate = total_debit - total_credit

            value_26 = value_calculate if value_calculate > 0 else 0
            value_27 = value_calculate if value_calculate < 0 else 0
            value_28 = abs(sum_sodu_no) - abs(sum_sodu_co) + abs(value_26) - abs(value_27)
            value_29 = total_debit + total_credit - value_26 + value_27
            for title in [(0,'- Cộng số phát sinh tháng'),(1,'- Số dư cuối tháng'),(2,'- Cộng lũy kế từ đầu quý')]:
                value1 = ''
                value2 = ''
                if title[0] == 0:
                    value1 = abs(total_debit if total_debit else 0)
                    value2 = abs(total_credit if total_credit else 0)
                if title[0] == 1:
                    value1 = abs(value_26 if value_26 else 0)
                    value2 = abs(value_27)
                if title[0] == 2:
                    value1 = (abs(value_28)) if value_28 > 0 else 0
                    value2 = (abs(value_28)) if value_28 < 0 else 0

                total_array.append((title[1],('{:,}'.format(int(value1))if value1 else '0','{:,}'.format(int(value2)) if value2 else '0')))
            array_line.append((value.get('balance'),line_show,total_array))

        vals = {
            'date': options.get('date'),
            'account_name': account_name,
            'account_code': account_code,
            'docs': self,
            'line_show': array_line,
            'total_array': total_array,
        }
        print_mode_self = self.with_context(print_mode=True)
        print_options = print_mode_self.get_options(previous_options=options)
        body_html = print_mode_self.get_html_custom(print_options,vals)
        footer = self.env['ir.actions.report']._render_template("biz_ledger_according_to_circular_no_200.internal_layout_custom", values=rcontext)
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
            'file_name': _('Sổ cái (mẫu số S03b-DN)'),
            'file_content': file_content,
            'file_type': 'pdf',
        }
    
    def get_html_custom(self,print_options,render_values):
        html = self.env['ir.qweb']._render('biz_ledger_according_to_circular_no_200.S03B_DN_template', render_values)
        return html
        
    def _get_styles(self, workbook):
        format_common = {'font_name': 'Times New Roman', 'font_size': 13}
        return {
            'INTRO': {
                'sub_title_format': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'bold': True, 'top': 2}),
                'unit': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'right', 'bold': True, 'left': 2}),
                'unit_content': workbook.add_format({**format_common, 'text_wrap': True, 'bold': True, 'align': 'left', }),
                'circulars_row2': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'italic': True}),
                'bold_right': workbook.add_format({**format_common, 'text_wrap': True, 'right': 2}),
                'text_right': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'right'}),
                'text_center': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center','bold': True}),
                'text_center_sign': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center','italic': True}),
                'text_left': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'left'}),
                'bold_left': workbook.add_format({**format_common, 'text_wrap': True, 'left': 2}),
                'address_content': workbook.add_format({**format_common,'text_wrap': True, 'align': 'left'}),
                'title': workbook.add_format({'font_name': 'Times New Roman', 'font_size': 16, 'bold': True, 'text_wrap': True, 'align': 'center'}),
                'title_explanation': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'bold': True}),
            },
            'TABLE': {
                'col_no_line_center': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 0, 'top': 0, 'left': 1, 'right':1}),
                'col_no_line_center_right': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'right', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 0, 'top': 0, 'left': 1, 'right':1}),
                'col_no_line_center_left': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'left', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 0, 'top': 0, 'left': 1, 'right':1}),
                'col_no_line_bottom': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 0, 'top': 1, 'left': 1, 'right':1}),
                'col_no_line_bottom_right': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'right', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 0, 'top': 1, 'left': 1, 'right':1}),
                'col_no_line_bottom_left': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'left', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 0, 'top': 1, 'left': 1, 'right':1}),
                'col_no_line_top': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 1, 'top': 0, 'left': 1, 'right':1}),
                'col_no_line_top_left': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'left', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 1, 'top': 0, 'left': 1, 'right':1}),
                'col_no_line_top_right': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'right', 'valign': 'vcenter', 'bold': True, 'bg_color': '#FFFFFF','font_color': '000000', 'bottom': 1, 'top': 0, 'left': 1, 'right':1}),
                'col_title': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'bottom': 1, 'top': 1, 'left': 1, 'right':1}),
                'col_value': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter',  'font_color': '000000', 'bottom': 1, 'top': 1, 'left': 1, 'right':1}),
                'col_value_left': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'left', 'valign': 'vcenter',  'font_color': '000000', 'bottom': 1, 'top': 1, 'left': 1, 'right':1}),
                'col_value_right': workbook.add_format({**format_common, 'text_wrap': True, 'align': 'right', 'valign': 'vcenter',  'font_color': '000000', 'bottom': 1, 'top': 1, 'left': 1, 'right':1}),
            }
        }
    
    def get_address_by(self, company):
        address_parts = []

        if company and company.street:
            address_parts.append(company.street)

        if company and company.street2:
            address_parts.append(company.street2)

        if company and company.city:
            address_parts.append(company.city)

        if company and company.state_id:
            address_parts.append(company.state_id.name)

        if company and company.country_id:
            address_parts.append(company.country_id.name)

        address = ', '.join(address_parts)
        return address

    # Sổ cái
    def export_general_ledger_xlsx(self, options, response=None):
        if not options.get('account_ids'):
            raise ValidationError('Vui lòng chọn tài khoản')
        options['unfold_all'] = True
        report = self.env.ref('account_reports.general_ledger_report')

        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        sheet = workbook.add_worksheet(self.name[:31])
        styles = self._get_styles(workbook)
        sheet.hide_gridlines(2)

        sheet.merge_range('G1:J1', 'Mẫu số SO3b-DN', styles['INTRO']['sub_title_format'])
        sheet.merge_range('A1:B1', 'Đơn vị:', styles['INTRO']['unit'])
        unit_content = '    %s   ' % (self.env.company.name if self.env.company else '')
        sheet.merge_range('C1:F1', unit_content, styles['INTRO']['unit_content'])
        sheet.merge_range('G2:J2', '(Ban hành theo Thông tư số 200/2014/TT-BTC', styles['INTRO']['circulars_row2'])
        sheet.merge_range('A2:B3', 'Địa chỉ:', styles['INTRO']['unit'])
        address_content = '    %s   ' % (self.get_address_by(self.env.company) if self.env.company else '')
        sheet.merge_range('C2:F3', address_content, styles['INTRO']['address_content'])
        sheet.merge_range('G3:J3', 'Ngày 22/12/2014 của Bộ Tài chính)', styles['INTRO']['circulars_row2'])

        # Tiêu đề
        sheet.set_row(6, 20)
        sheet.merge_range('D7:H7', 'SỔ CÁI', styles['INTRO']['title'])
        title_explanation = '(Dùng cho hình thức kết toán Nhật ký chung)'
        sheet.merge_range('D8:H8', title_explanation, styles['INTRO']['title_explanation'])
        
        # time
        date = options.get('date')

        string = self.get_string_filter(date)    
            
        time = string if string else '....'
        sheet.merge_range('D9:H9', time, styles['INTRO']['title_explanation'])

        # Tên tk:
        account = options.get('account_ids',[])

        account_ids = self.env['account.account'].sudo().search([('id','in',account)])

        account_name = 'Tên tài khoản: %s'  %(self.mapped_account(account_ids,value='name'))
        sheet.merge_range('D10:H10', account_name, styles['INTRO']['title_explanation'])

        account_code = 'Số hiệu: %s' %(self.mapped_account(account_ids,value='code'))
        sheet.merge_range('D11:H11', account_code, styles['INTRO']['title_explanation'])

        # TABLE
        sheet.merge_range('A13:B14', 'Ngày, tháng ghi sổ', styles['TABLE']['col_title'])
        sheet.merge_range('C13:D13', 'Chứng từ', styles['TABLE']['col_title'])
        sheet.write('C14', 'Số hiệu', styles['TABLE']['col_title'])
        sheet.write('D14', 'Ngày tháng', styles['TABLE']['col_title'])
        sheet.merge_range('E13:E14', 'Diễn giải', styles['TABLE']['col_title'])
        sheet.merge_range('F13:G13', 'Nhật ký chung', styles['TABLE']['col_title'])
        sheet.write('F14', 'Trang sổ', styles['TABLE']['col_title'])
        sheet.write('G14', 'STT dòng', styles['TABLE']['col_title'])
        sheet.write('H13', 'Số hiệu', styles['TABLE']['col_title'])
        sheet.write('H14', 'TK đối ứng', styles['TABLE']['col_title'])
        sheet.merge_range('I13:J13', 'Số tiền', styles['TABLE']['col_title'])
        sheet.write('I14', 'Nợ', styles['TABLE']['col_title'])
        sheet.write('J14', 'Có', styles['TABLE']['col_title'])

        y_offset = 14
        sheet.merge_range(y_offset, 0,y_offset, 1, 'A', styles['TABLE']['col_title'])
        sheet.write(y_offset, 2, 'B', styles['TABLE']['col_title'])
        sheet.write(y_offset, 3, 'C', styles['TABLE']['col_title'])
        sheet.write(y_offset, 4, 'D', styles['TABLE']['col_title'])
        sheet.write(y_offset, 5, 'E', styles['TABLE']['col_title'])
        sheet.write(y_offset, 6, 'G', styles['TABLE']['col_title'])
        sheet.write(y_offset, 7, 'H', styles['TABLE']['col_title'])
        sheet.write(y_offset, 8, '1', styles['TABLE']['col_title'])
        sheet.write(y_offset, 9, '2', styles['TABLE']['col_title'])
        y_offset += 1

        array_acc = []
        
        for acc in account_ids:
            array_acc.append(report._get_generic_line_id('account.account', acc.id))

        for lines in array_acc:
            model, model_id = report._get_model_info_from_id(lines)
            account, init_balance_by_col_group = self.env['account.general.ledger.report.handler']._get_initial_balance_values(report, [model_id], options)[model_id]

            value = list(init_balance_by_col_group.values())[0]

            aml_results = self.env['account.general.ledger.report.handler']._get_aml_values(report, options, [model_id])
            aml_results = list(aml_results)[0][model_id] if aml_results else []

            sum_sodu_no = value.get('balance') if value.get('balance') and value.get('balance') > 0 else 0
            sum_sodu_co = value.get('balance') if value.get('balance') and value.get('balance') < 0 else 0

            line_show = self.get_lines_xlsx(aml_results)
            sheet.merge_range(y_offset, 0,y_offset, 1, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 2, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 3, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 4, '- Số dư đầu năm', styles['TABLE']['col_no_line_bottom_left'])
            sheet.write(y_offset, 5, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 6, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 7, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 8, '{:,}'.format(int(abs(value.get('balance')))) if value.get('balance') and value.get('balance') > 0 else '', styles['TABLE']['col_no_line_bottom_right'])
            sheet.write(y_offset, 9, '{:,}'.format(int(abs(value.get('balance')))) if value.get('balance') and value.get('balance') < 0 else '', styles['TABLE']['col_no_line_bottom_right'])
            y_offset += 1
            sheet.merge_range(y_offset, 0,y_offset, 1, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 2, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 3, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 4, '- Số phát sinh trong tháng', styles['TABLE']['col_no_line_top_left'])
            sheet.write(y_offset, 5, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 6, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 7, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 8, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 9, '', styles['TABLE']['col_no_line_top'])
            y_offset += 1

            total_debit = 0
            total_credit = 0
            for line in line_show:
                col_value_style = styles['TABLE']['col_value']
                for key, val in line.items():
                    if key == 'column7':
                        total_debit += val if val else 0
                        val = '{:,}'.format(int(val)) if val else 0
                        col_value_style = styles['TABLE']['col_value_right']
                    if key == 'column8':
                        total_credit += val if val else 0
                        val = '{:,}'.format(int(val)) if val else 0
                        col_value_style = styles['TABLE']['col_value_right']

                    if key == 'column0':
                        sheet.merge_range(y_offset, 0,y_offset, 1, val, col_value_style)
                    else:
                        if key == 'column3':
                            col_value_style = styles['TABLE']['col_value_left']
                        sheet.write(y_offset, cols[key] + 1, val, col_value_style)

                y_offset +=1

            value_calculate = total_debit - total_credit

            value_26 = value_calculate if value_calculate > 0 else 0
            value_27 = value_calculate if value_calculate < 0 else 0
            value_28 = abs(sum_sodu_no) - abs(sum_sodu_co) + abs(value_26) - abs(value_27)
            value_29 = total_debit + total_credit - value_26 + value_27
            sheet.merge_range(y_offset, 0,y_offset, 1, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 2, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 3, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 4, '- Cộng số phát sinh tháng', styles['TABLE']['col_no_line_bottom_left'])
            sheet.write(y_offset, 5, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 6, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 7, '', styles['TABLE']['col_no_line_bottom'])
            sheet.write(y_offset, 8, '%s' % '{:,}'.format(int(abs(total_debit))) if total_debit else 0, styles['TABLE']['col_no_line_bottom_right'])
            sheet.write(y_offset, 9, '%s' % '{:,}'.format(int(abs(total_credit))) if total_credit else 0, styles['TABLE']['col_no_line_bottom_right'])
            y_offset += 1
            sheet.merge_range(y_offset, 0,y_offset, 1, '', styles['TABLE']['col_no_line_center'])
            sheet.write(y_offset, 2, '', styles['TABLE']['col_no_line_center'])
            sheet.write(y_offset, 3, '', styles['TABLE']['col_no_line_center'])
            sheet.write(y_offset, 4, '- Số dư cuối tháng', styles['TABLE']['col_no_line_center_left'])
            sheet.write(y_offset, 5, '', styles['TABLE']['col_no_line_center'])
            sheet.write(y_offset, 6, '', styles['TABLE']['col_no_line_center'])
            sheet.write(y_offset, 7, '', styles['TABLE']['col_no_line_center'])
            sheet.write(y_offset, 8, '%s' % '{:,}'.format(int(abs(value_26))) if value_26 else 0, styles['TABLE']['col_no_line_center_right'])
            sheet.write(y_offset, 9, '%s' % '{:,}'.format(int(abs(value_27))) if value_27 else 0, styles['TABLE']['col_no_line_center_right'])
            y_offset += 1
            sheet.merge_range(y_offset, 0,y_offset, 1, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 2, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 3, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 4, '- Cộng lũy kế từ đầu quý', styles['TABLE']['col_no_line_top_left'])
            sheet.write(y_offset, 5, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 6, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 7, '', styles['TABLE']['col_no_line_top'])
            sheet.write(y_offset, 8, '%s' %  ('{:,}'.format(int(abs(value_28))) if value_28 > 0 else '0'), styles['TABLE']['col_no_line_top_right'])
            sheet.write(y_offset, 9, '%s' % ('{:,}'.format(int(abs(value_28))) if value_28 < 0 else '0'), styles['TABLE']['col_no_line_top_right'])
            y_offset +=1
        
        sheet.merge_range(y_offset, 0 , y_offset,  9, '- Sổ này có .... trang, đánh số từ trang số 01 đến trang ....', styles['INTRO']['text_left'])
        y_offset +=1
        sheet.merge_range(y_offset, 0 , y_offset,  9, '- Ngày mở sổ ....', styles['INTRO']['text_left'])
        y_offset +=1
        sheet.merge_range(y_offset, 0 , y_offset,  9, 'Ngày.... tháng.... năm ........', styles['INTRO']['text_right'])
        y_offset +=1
        sheet.merge_range(y_offset, 0 , y_offset,  3, 'Người ghi sổ', styles['INTRO']['text_center'])
        sheet.merge_range(y_offset, 4 , y_offset,  6, 'Kế toán trưởng', styles['INTRO']['text_center'])
        sheet.merge_range(y_offset, 7 , y_offset,  9, 'Người đại diện theo pháp luật', styles['INTRO']['text_center'])
        y_offset +=1
        sheet.merge_range(y_offset, 0 , y_offset,  3, '(Ký, họ tên)', styles['INTRO']['text_center_sign'])
        sheet.merge_range(y_offset, 4 , y_offset,  6, '(Ký, họ tên)', styles['INTRO']['text_center_sign'])
        sheet.merge_range(y_offset, 7 , y_offset,  9, '(Ký, họ tên, đóng dấu)', styles['INTRO']['text_center_sign'])

        y_offset +=1
        sheet.merge_range(y_offset, 0 , y_offset,  3, '', styles['INTRO']['text_center_sign'])
        sheet.merge_range(y_offset, 4 , y_offset,  6, '', styles['INTRO']['text_center_sign'])
        sheet.merge_range(y_offset, 7 , y_offset,  9, '', styles['INTRO']['text_center_sign'])

        sheet.set_row(y_offset,100)

        # set column
        sheet.set_column('A:A', 3)
        sheet.set_column('B:B', 14)
        sheet.set_column('C:C', 14)
        sheet.set_column('D:D', 14)
        sheet.set_column('E:E', 34)
        sheet.set_column('F:F', 14)
        sheet.set_column('G:G', 14)
        sheet.set_column('H:H', 14)
        sheet.set_column('I:I', 14)
        sheet.set_column('J:J', 14)
        sheet.set_column('K:K', 3)


        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return {
            'file_name': _('Sổ cái (mẫu số S03b-DN)'),
            'file_content': generated_file,
            'file_type': 'xlsx',
        }

    def mapped_account(self,account_ids,value=False):
        return (','.join(account_ids.mapped(value)) if account_ids else '...')

    def get_string_filter(self,options):
        mode = options.get('mode')
        period_type = options.get('period_type')
        date_to = datetime.strptime(options.get('date_to'),'%Y-%m-%d')
        date_from = datetime.strptime(options.get('date_from'),'%Y-%m-%d')

        if mode == 'single':
            string = _('Kể từ %s') % (format_date(self.env, fields.Date.to_string(date_to)))
        elif period_type == 'year' or (
            period_type == 'fiscalyear' and (date_from, date_to) == date_utils.get_fiscal_year(date_to)):
            string = _('Năm %s') % (date_to.strftime('%Y'))
        elif period_type == 'fiscalyear' and (date_from, date_to) == date_utils.get_fiscal_year(date_to, day=fy_day, month=fy_month):
            string = '%s - %s' % (date_to.year - 1, date_to.year)
        elif period_type == 'month':
            string = _('Tháng %s năm %s') % (date_to.strftime('%m'),date_to.strftime('%Y'))
        elif period_type == 'quarter':
            string = _('Quý %s năm %s') %(date_utils.get_quarter_number(date_to),date_to.year)
        else:
            dt_from_str = format_date(self.env, fields.Date.to_string(date_from))
            dt_to_str = format_date(self.env, fields.Date.to_string(date_to))
            string = _('Từ %s\nđến  %s') % (dt_from_str, dt_to_str)
        return string
    
    def get_lines_xlsx(self,data):
        vals = []
        for k,v in data.items():
            item = list(v.values())[0]
            move_line = self.env['account.move.line'].browse(int(item.get('id')))
            move = move_line.move_id
            check = False
            if len(move.line_ids) >= 3:
                if move_line.credit > 0 or move_line.debit > 0:
                    credit = True if move_line.credit > 0 else False
                    lines = move.line_ids.filtered(lambda x: x.id != move_line.id)
                    if not lines.filtered(lambda x: (x.credit > 0 if credit else x.debit > 0)):
                        check = True
                        for line in lines:
                            vals.append({
                                'column0': k[1].strftime('%d/%m/%Y'),
                                'column1': item.get('move_name'),
                                'column2': k[1].strftime('%d/%m/%Y'),
                                'column3': line.name,
                                'column4': '',
                                'column5': '',
                                'column6': ','.join(line.account_id.mapped('code')) if line.account_id else '',
                                'column7': line.credit,
                                'column8': line.debit,
                            })
            if not check:
                vals.append({
                    'column0': k[1].strftime('%d/%m/%Y'),
                    'column1': item.get('move_name'),
                    'column2': k[1].strftime('%d/%m/%Y'),
                    'column3': item.get('communication'),
                    'column4': '',
                    'column5': '',
                    'column6': ','.join(move_line.ctp_account_ids.mapped('code')) if move_line.ctp_account_ids else '',
                    'column7': abs(item.get('balance')) if item.get('balance') > 0 else '',
                    'column8': abs(item.get('balance')) if item.get('balance') < 0 else '',
                })

        return vals
    

    def get_all_total(self,report,options):
        date_from = fields.Date.from_string(options['date']['date_from'])
        totals_by_column_group = defaultdict(lambda: {'debit': 0, 'credit': 0, 'balance': 0})
        for account, column_group_results in self.env['account.general.ledger.report.handler']._query_values(report, options):
            eval_dict = {}
            has_lines = False
            for column_group_key, results in column_group_results.items():
                account_sum = results.get('sum', {})
                account_un_earn = results.get('unaffected_earnings', {})

                account_debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
                account_credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
                account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

                eval_dict[column_group_key] = {
                    'amount_currency': account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    'debit': account_debit,
                    'credit': account_credit,
                    'balance': account_balance,
                }

                max_date = account_sum.get('max_date')
                has_lines = has_lines or (max_date and max_date >= date_from)

                totals_by_column_group[column_group_key]['debit'] += account_debit
                totals_by_column_group[column_group_key]['credit'] += account_credit
                totals_by_column_group[column_group_key]['balance'] += account_balance
        return totals_by_column_group