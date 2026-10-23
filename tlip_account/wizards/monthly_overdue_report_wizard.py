from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from itertools import groupby

INVOICE_TYPE_UTILITY_MAPPING = {
    'electricity': 'Power',
    'water': 'Water',
    'rental_fee': 'Rental',
    'management_fee': 'Management Fee'
}

MAX_OVERDUE_INVOICES_COUNT = 3


class MonthlyOverdueReportWizard(models.TransientModel):
    _name = 'monthly.overdue.report.wizard'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Monthly Overdue Report Wizard'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("Start Date cannot be after End Date.")

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            self.start_date = self.start_date.replace(day=1)

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date:
            self.end_date = self.end_date.replace(day=1) + relativedelta(months=1, days=-1)

    def action_generate_overdue_report(self):
        self.ensure_one()
        action = self.env['ir.actions.report']._for_xml_id('tlip_account.action_print_overdue_invoice_report_xlsx')
        action['context'] = {**self.env.context, 'overdue_wizard': self}
        return action


class MonthlyOverdueReportXlsx(models.AbstractModel):
    _name = 'report.tlip_account.monthly_overdue_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Monthly Overdue Report XLSX'

    def _get_report_styles(self, workbook):
        """Returns predefined styles for the report."""
        base_style = {
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
            'font_size': 12,
            'border': 1,
            'text_wrap': True
        }
        return {
            'sheet_1': {
                'top_header': workbook.add_format({**base_style, 'font_size': 18, 'bold': True, 'align': 'center'}),
                'child_header_1': workbook.add_format({**base_style, 'bold': True, 'align': 'center', 'bg_color': '#bdd6ee'}),
                'child_header_2': workbook.add_format({**base_style, 'bold': True, 'align': 'center', 'bg_color': '#8eaadb'}),
                'child_header_3': workbook.add_format({**base_style, 'bold': True, 'align': 'center', 'bg_color': '#f0f000'}),
                'odd_month_header': workbook.add_format({**base_style, 'bold': True, 'align': 'center', 'bg_color': '#b4c6e7'}),
                'even_month_header': workbook.add_format({**base_style, 'bold': True, 'align': 'center', 'bg_color': '#c5e0b3'}),
                'cell': workbook.add_format({**base_style, 'font_size': 11, 'align': 'center'}),
                'tenant_cell': workbook.add_format({**base_style, 'font_size': 11}),
            },
            'sheet_2': {
                'top_header': workbook.add_format({**base_style, 'bold': True, 'border': 0, 'align': 'center'}),
                'child_header': workbook.add_format({**base_style, 'bold': True, 'bg_color': '#acb9ca', 'align': 'center'}),
                'cell': workbook.add_format({**base_style, 'align': 'center'}),
                'italic_cell': workbook.add_format({**base_style, 'italic': True, 'border': 0}),
                'blank_cell': workbook.add_format({**base_style, 'bg_color': '#e2efd9'}),
            }
        }

    def generate_xlsx_report(self, workbook, data, overdue_wizard):
        sorted_overdue_invoices = self._get_overdue_invoices()
        # first worksheet
        self._render_monthly_overdue_sheet(workbook, sorted_overdue_invoices, overdue_wizard)
        # second worksheet
        self._render_consecutive_overdue_sheet(workbook, sorted_overdue_invoices, overdue_wizard)

    def _get_overdue_invoices(self):
        """Fetches and groups overdue invoices by partner."""
        today = fields.Date.today()
        invoices = self.env['account.move'].search([
            ('is_overdue_invoice', '=', True),
            ('invoice_date_due', '>=', f'{today.year}-01-01'),
            ('invoice_date_due', '<=', f'{today.year}-12-31'),
            ('company_id', '=', self.env.company.id),
        ])

        # groupby invoices by partner
        sorted_invoices = invoices.sorted(key=lambda inv: inv.partner_id.id)
        return sorted_invoices
        
    def _render_monthly_overdue_sheet(self, workbook, overdue_invoices, overdue_wizard):
        overdue_invoices = groupby(overdue_invoices, key=lambda inv: inv.partner_id)
        """Writes the header section of the report."""
        today = fields.Date.today()
        sheet = workbook.add_worksheet('Monthly overdue report')
        styles = self._get_report_styles(workbook).get('sheet_1')
        sheet.merge_range(0, 0, 0, 20, 'SUMMARY OVERDUE REPORT', styles['top_header'])
        
        # Row 2 - Header
        sheet.write(1, 0, '', styles['child_header_1'])
        sheet.write(1, 1, '', styles['child_header_1'])
        sheet.merge_range(1, 2, 1, 7, f"Total overdue in Y{today.year}", styles['child_header_2'])
        sheet.merge_range(1, 8, 1, 9, 'Deposit times', styles['child_header_2'])
        sheet.merge_range(1, 10, 1, 13, 'Check 3 consecutive overdue times', styles['child_header_2'])
        sheet.merge_range(1, 14, 1, 19, f"From {overdue_wizard.start_date} to {overdue_wizard.end_date}", styles['child_header_2'])
        sheet.merge_range(1, 20, 2, 20, "Accumulated total until this month", styles['child_header_2'])

        sheet.set_column('B:B', 35)
        sheet.set_column('U:U', 13)

        # Row 3 - Column headers
        headers = [
            'No', 'Name of Tenant', 'Power', 'Water', 'Rental', 'Management Fee', 'Other Fee', 'Sub-Total',
            'Power', 'Water', 'Power', 'Note', 'Water', 'Note', 'PC', 'WC', 'RF', 'MF', 'OT', 'Total'
        ]
        curr_row = 2  # Start below the header
        for col, header in enumerate(headers[:2]):
            sheet.write(curr_row, col, header, styles['child_header_1'])

        for col, header in enumerate(headers[2:]):
            sheet.write(curr_row, col + 2, header, styles['child_header_2'])

        curr_row = 3
        for col, _ in enumerate(headers):
            sheet.write(curr_row, col, '', styles['child_header_3'])

        account_move_env = self.env['account.move']

        CONTENT_START_ROW = 4
        curr_row = CONTENT_START_ROW

        for idx, (partner, invoices) in enumerate(overdue_invoices, start=1):
            sheet.write(curr_row, 0, idx, styles['cell'])
            sheet.write(curr_row, 1, partner.name, styles['tenant_cell'])
            invoices = self.env['account.move'].concat(*invoices)

            # Total overdue in Y{today.year}
            invoices_by_utility = self._group_overdue_invoices_by_utility_type(invoices)
            sheet.write_row(curr_row, 2, [len(invoices_by_utility.get(utility, [])) for utility in ['Power', 'Water', 'Rental', 'Management Fee', 'Other Fee']], styles['cell'])
            sheet.write(curr_row, 7, len(invoices), styles['cell'])

            # Deposit times
            deposit_counts = {utility: len(account_move_env.concat(*invoices_by_utility.get(utility, [])).mapped('deposit_payment_id')) for utility in ['Power', 'Water']}
            sheet.write_row(curr_row, 8, [deposit_counts.get('Power', 0), deposit_counts.get('Water', 0)], styles['cell'])

            # Check 3 consecutive overdue times
            overdue_counts = {utility: len(invoices_by_utility.get(utility, [])) - deposit_counts.get(utility, 0) for utility in ['Power', 'Water']}
            sheet.write(curr_row, 10, overdue_counts.get('Power', 0) % MAX_OVERDUE_INVOICES_COUNT, styles['cell'])
            sheet.write(curr_row, 11, '', styles['cell']) # empty note
            sheet.write(curr_row, 12, overdue_counts.get('Water', 0) % MAX_OVERDUE_INVOICES_COUNT, styles['cell'])
            sheet.write(curr_row, 13, '', styles['cell']) # empty note

            # Overdue invoices within input period
            filtered_invoices = account_move_env.concat(*invoices).filtered(lambda inv: overdue_wizard.start_date <= inv.invoice_date_due <= overdue_wizard.end_date)
            period_invoices_by_utility = self._group_overdue_invoices_by_utility_type(filtered_invoices)
            sheet.write_row(curr_row, 14, [len(period_invoices_by_utility.get(utility, [])) for utility in ['Power', 'Water', 'Rental', 'Management Fee', 'Other Fee']], styles['cell'])
            sheet.write(curr_row, 19, len(filtered_invoices), styles['child_header_3'])
            curr_row += 1

        # Total row
        next_col = 'C'
        sheet.write(curr_row, 1, 'Total', styles['child_header_3'])
        for col, _ in enumerate(headers[2:]):
            sheet.write_formula(curr_row, col + 2, f"SUM({next_col}{CONTENT_START_ROW}:{next_col}{curr_row})", styles['child_header_3'])
            next_col = chr(ord(next_col) + 1)


    def _group_overdue_invoices_by_utility_type(self, invoices):
        """Groups overdue invoices by utility type."""
        grouped_invoices = {}
        for invoice in invoices:
            utility_type = INVOICE_TYPE_UTILITY_MAPPING.get(invoice.invoice_type_id.utility_type, 'Other Fee')
            grouped_invoices.setdefault(utility_type, []).append(invoice)
        return grouped_invoices


    def _render_consecutive_overdue_sheet(self, workbook, overdue_invoices, overdue_wizard):
        """Creates the overdue invoice worksheet with formatted headers."""
        overdue_invoices_by_partner = groupby(overdue_invoices, key=lambda inv: inv.partner_id)
        sheet = workbook.add_worksheet('3 consecutive times - Deposit')
        
        # Get styles
        styles = self._get_report_styles(workbook).get('sheet_2')
        top_header = styles['top_header']
        child_header = styles['child_header']
        italic_cell = styles['italic_cell']
        blank_cell = styles['blank_cell']
        
        # Title and general headers
        sheet.merge_range('A2:V2', 'LIST OF TENANTS OVERDUE 3 CONSECUTIVE TIMES', top_header)
        sheet.write('U4', 'Unit: VND', italic_cell)
        
        # Column headers
        headers = [
            ('A5:A7', 'No.'), ('B5:B7', 'Tenant code'), ('C5:C7', 'Tenant name'), ('D5:D7', 'Category'),
            ('E5:I5', '1st times overdue'), ('E6:F6', 'Invoice'), ('E7', 'No.'), ('F7', 'Date'),
            ('G6:G7', 'Amount'), ('H6:H7', 'Due date'), ('I6:I7', 'Paid date'),
            ('J5:N5', '2nd times overdue'), ('J6:K6', 'Invoice'), ('J7', 'No.'), ('K7', 'Date'),
            ('L6:L7', 'Amount'), ('M6:M7', 'Due date'), ('N6:N7', 'Paid date'),
            ('O5:S5', '3rd times overdue'), ('O6:P6', 'Invoice'), ('O7', 'No.'), ('P7', 'Date'),
            ('Q6:Q7', 'Amount'), ('R6:R7', 'Due date'), ('S6:S7', 'Paid date'),
            ('T5:V5', 'Deposit'), ('T6:T7', 'Amount'), ('U6:U7', 'Paid date'), ('V6:V7', 'Repayment date')
        ]
        
        for rng, text in headers:
            sheet.merge_range(rng, text, child_header) if ':' in rng else sheet.write(rng, text, child_header)
        
        # Column width settings
        sheet.set_column('C:C', 25)
        sheet.set_column('E:V', 16)
        
        # Add a blank line
        row = 7
        for col in range(22):
            sheet.write(row, col, '', blank_cell)

        idx = 0
        for partner, invoices in overdue_invoices_by_partner:
            invoices = self.env['account.move'].concat(*invoices)
            consecutive_invoices = invoices.filtered(lambda inv: inv.deposit_payment_id and overdue_wizard.start_date <= inv.invoice_date_due <= overdue_wizard.end_date)
            deposit_payments = consecutive_invoices.mapped('deposit_payment_id')
            for deposit_payment in deposit_payments:
                idx += 1
                row += 1

                related_invoices = deposit_payment.overdue_move_ids
                invoice_type = related_invoices.mapped('invoice_type_id')
                detail_type = invoice_type.utility_type or invoice_type.leasing_type or 'Other Fee'

                sheet.write(row, 0, idx, styles['cell'])
                sheet.write(row, 1, partner.customer_code or '', styles['cell'])
                sheet.write(row, 2, partner.name, styles['cell'])
                sheet.write(row, 3, INVOICE_TYPE_UTILITY_MAPPING.get(detail_type, 'Other Fee'), styles['cell'])
                start_col = 4
                for inv in related_invoices:
                    sheet.write(row, start_col, inv.name, styles['cell'])
                    invoice_date = inv.invoice_date and inv.invoice_date.strftime('%Y-%m-%d') or 'N/A'
                    invoice_date_due = inv.invoice_date_due and inv.invoice_date_due.strftime('%Y-%m-%d') or 'N/A'
                    sheet.write(row, start_col + 1, invoice_date, styles['cell'])
                    sheet.write(row, start_col + 2, inv.amount_total, styles['cell'])
                    sheet.write(row, start_col + 3, invoice_date_due, styles['cell'])
                    paid_date = ''
                    if inv.amount_residual == 0:
                        latest_payment = sorted(inv.mapped('matched_payment_ids'))
                        paid_date = latest_payment and latest_payment[-1].date or ''
                    sheet.write(row, start_col + 4, paid_date, styles['cell'])
                    start_col += 5

                start_col = 19
                sheet.write(row, start_col, deposit_payment.amount, styles['cell'])
                date = deposit_payment.date and deposit_payment.date.strftime('%Y-%m-%d') or 'N/A'
                due_date = deposit_payment.due_date and deposit_payment.due_date.strftime('%Y-%m-%d') or 'N/A'
                sheet.write(row, start_col + 1, date, styles['cell'])
                sheet.write(row, start_col + 2, due_date, styles['cell'])