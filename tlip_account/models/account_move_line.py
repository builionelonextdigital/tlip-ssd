from dateutil.relativedelta import relativedelta
import calendar
from datetime import date
from dateutil import rrule

from odoo import api, fields, models, _, Command
from odoo.tools import float_is_zero, formatLang, float_round
from odoo.tools.date_utils import end_of
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    approval_readonly = fields.Boolean(related='move_id.approval_readonly')
    line_no = fields.Integer(
        string="No.",
        compute='_compute_line_no',
        store=True,
        readonly=False
    )
    area = fields.Float('Area (m2)', digits=(16, 2))
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    name = fields.Char(string='Description')
    analytic_distribution = fields.Json(string="Budget Code", compute='_compute_analytic_distribution', store=True)
    leasing_price_unit = fields.Float(string='Leasing Unit Price', digits='Product Price')
    oos_mapping_id = fields.Many2one('oos.mapping', string='OOS Mapping')
    invoice_number = fields.Char(string='Invoice Number')
    invoice_series = fields.Char(string='Invoice Series')
    request_payment_number = fields.Char(compute='_compute_request_payment_data', store=True, readonly=False, string='Resquest Payment Ref')
    request_payment_date = fields.Date(compute='_compute_request_payment_data', store=True, readonly=False)
    payment_note = fields.Text(string='Payment Note')
    invoice_date = fields.Date(readonly=False)
    tax_excluded = fields.Monetary(string='Tax Excluded', currency_field='currency_id')
    payment_note = fields.Text(string='Payment Note')
    entry_currency_rate = fields.Float(
        compute='_compute_data_journal_entry',
        store=True, readonly=False,
        string='Currency Rate',
    )
    land_plot_id = fields.Many2one(
        comodel_name='stock.location',
        compute='_compute_data_journal_entry',
        store=True, readonly=False,
        string="Location",
        check_company=True
    )
    development_project_id = fields.Many2one(
        comodel_name='development.project',
        compute='_compute_data_journal_entry',
        store=True, readonly=False,
        string='Project Name',
        check_company=True
    )
    development_project_code = fields.Char(
        compute='_compute_data_journal_entry',
        store=True,
        string='Project Code',
    )
    development_phase_id = fields.Many2one(
        comodel_name='development.phase',
        compute='_compute_data_journal_entry',
        store=True, readonly=False,
        string='Phase',
        check_company=True
    )
    contract_number = fields.Char(
        compute='_compute_data_journal_entry',
        store=True, readonly=False,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Goods / Service',
        inverse='_inverse_product_id',
        ondelete='restrict',
        check_company=True,
    )

    @api.constrains('account_id', 'display_type')
    def _check_payable_receivable(self):
      lines_to_check = self.env['account.move.line']
      for line in self:
          # Allow bypass for receivable accounts
          if line.account_id.account_type == 'asset_receivable':
              continue
          lines_to_check |= line

      if lines_to_check:
          super(AccountMoveLine, lines_to_check)._check_payable_receivable()

    @api.constrains('date_from', 'date_to')
    def _check_deferred_dates(self):
        for line in self:
            if line.date_from and line.date_to and line.date_from > line.date_to:
                raise UserError(_(f"{line.name} - Date From must be less than or equal to Date To"))
            
    @api.depends('move_id.request_payment_number')
    def _compute_request_payment_data(self):
        for record in self:
            record.request_payment_number = record.move_id.request_payment_number if record.move_id.request_payment_number else record.request_payment_number
            record.request_payment_date = record.move_id.request_payment_date if record.move_id.request_payment_number else record.request_payment_date

    @api.depends('move_id.invoice_line_ids', 'move_id.invoice_line_ids.sequence')
    def _compute_line_no(self):
        for move in self.mapped('move_id'):
            lines = move.invoice_line_ids.sorted(key=lambda r: r.sequence)
            current_no = 1
            previous_line = False

            for line in lines:
                # Skip existing records with unchanged valid numbers
                if line._origin and line._origin.line_no and line._origin.line_no == line.line_no:
                    previous_line = line                        
                    current_no = max(current_no, line.line_no + 1)
                    continue

                if not line.line_no:
                    if line._origin and previous_line and previous_line.line_no:
                        line.line_no = previous_line.line_no
                        current_no = line.line_no + 1
                    else:
                        line.line_no = current_no
                        current_no += 1
                else:
                    line.line_no = current_no
                    current_no = max(current_no, line.line_no + 1)
                
                previous_line = line

    @api.depends('product_id')
    def _compute_analytic_distribution(self):
        for line in self:
            if line.product_id and not line.purchase_line_id:
                analytic_distribution = line.analytic_distribution
                if line.move_id.is_sale_document(include_receipts=True) and line.product_id.income_budget_code_id:
                    analytic_account = line.product_id.income_budget_code_id._get_analytic_account(line.company_id.id)
                    analytic_distribution = {analytic_account.id: 100}
                elif line.move_id.is_purchase_document(include_receipts=True) and line.product_id.expense_budget_code_id:
                    analytic_account = line.product_id.expense_budget_code_id._get_analytic_account(line.company_id.id)
                    analytic_distribution = {analytic_account.id: 100}
                line.analytic_distribution = analytic_distribution
            else:
                line.analytic_distribution = line.analytic_distribution

    @api.depends('currency_id', 'company_id', 'move_id.entry_currency_rate',
                 'move_id.currency_id', 'move_id.invoice_currency_rate', 'move_id.date')
    def _compute_currency_rate(self):
        for line in self:
            if line.currency_id:
                move = line.move_id
                currency_rate = move.invoice_currency_rate
                if not move.is_invoice(True) and move.entry_currency_rate:
                    currency_rate = 1 / move.entry_currency_rate
                line.currency_rate = currency_rate
            else:
                line.currency_rate = 1

    @api.depends(
        "product_id",
        "move_id.ref",
        "move_id.payment_reference",
        "move_id.land_plot_id",
        "date_from",
        "date_to",
    )
    def _compute_name(self):
        # Keep the original name for payment term lines after posting
        payment_term_lines = self.filtered(lambda l: l.display_type == 'payment_term' and l.move_id.state == 'posted' and l.name)
        for line in payment_term_lines:
            line.name = line.name

        super(AccountMoveLine, self - payment_term_lines)._compute_name()
        date_format = self.env["res.lang"]._lang_get(
            self.env.user.lang).date_format
        for rec in self:
            name = rec.name
            if (
                rec.product_id
                and rec.move_id.land_plot_id
                and rec.date_from
                and rec.date_to
            ):
                land_plot_name = rec.move_id.land_plot_id.name
                date_from = rec.date_from.strftime(date_format)
                date_to = rec.date_to.strftime(date_format)
                name = "%s từ ngày %s đến ngày %s (%s from %s to %s)" % (
                    ' '.join(
                        filter(None, [rec.product_id.invoice_description_vn, land_plot_name])),
                    date_from,
                    date_to,
                    ' '.join(
                        filter(None, [rec.product_id.invoice_description_en, land_plot_name])),
                    date_from,
                    date_to,
                )
            elif rec.product_id.invoice_description_vn and rec.product_id.invoice_description_en:
                name = f"{rec.product_id.invoice_description_vn} ({rec.product_id.invoice_description_en})"
            rec.name = name

    @api.onchange('analytic_distribution')
    def _onchange_analytic_distribution(self):
        if self.analytic_distribution:
            budget_code_ids = list(dict(self.analytic_distribution).keys())
            if len(budget_code_ids) == 1 and budget_code_ids[0] != 'false':
                analytic_account = self.env["account.analytic.account"].browse(int(budget_code_ids[0]))
                budget_code = analytic_account.budget_code_id.with_context(company_id=self.company_id.id)
                self.account_id = budget_code.default_account_id

    def _compute_account_id(self):
        posted_lines = self.filtered(lambda l: l.move_id.state == 'posted')
        if posted_lines:
            # For posted lines, we keep the original account_id
            # This called since we allow user to change partner in account move line
            # _post function will re-compute partner_id and trigger _compute_account_id
            for line in posted_lines:
                line.account_id = line.account_id

        self = self - posted_lines
        current_period = self.env['accounting.period.closing']._get_current_accounting_period()
        accounting_period = current_period.accounting_period
        AnalyticAccount = self.env["account.analytic.account"]
        super(AccountMoveLine, self)._compute_account_id()
        for line in self:
            account_id = line.account_id
            move = line.move_id
            if line.display_type == 'product':
                is_deferred_amount = line.date_to > accounting_period if line.date_to and accounting_period else False
                if is_deferred_amount:
                    if move.move_type == 'out_invoice':
                        account_id = line.product_id.property_deferred_account_income_categ_id
                    elif move.move_type == 'in_invoice':
                        account_id = line.product_id.property_deferred_account_expense_categ_id
                elif line.analytic_distribution:
                    budget_code_ids = list(dict(line.analytic_distribution).keys())
                    if len(budget_code_ids) == 1 and budget_code_ids[0] != 'false':
                        analytic_account = AnalyticAccount.browse(int(budget_code_ids[0]))
                        budget_code = analytic_account.budget_code_id.with_context(company_id=self.company_id.id)
                        account_id = budget_code.default_account_id
            elif line.display_type == 'payment_term' and line.move_id.paid_by == 'employee' and line.move_id.move_type == 'in_invoice':
                replace_account_id = move.with_company(
                    move.company_id).employee_id.property_account_payable_id
                account_id = replace_account_id
            else:
                account_id = line.account_id
            line.account_id = account_id or line.account_id

    def _compute_partner_id(self):
        for line in self:
            if line.display_type == 'payment_term' and line.move_id.paid_by == 'employee' and line.move_id.move_type == 'in_invoice':
                line.partner_id = line.move_id.employee_id
            else:
                line.partner_id = line.move_id.partner_id.commercial_partner_id

    @api.depends(
        "move_id.entry_currency_rate",
        "move_id.land_plot_id",
        "move_id.development_project_id",
        "move_id.development_project_id.code",
        "move_id.development_phase_id",
        "move_id.contract_number",
        "development_project_id",
        "development_project_id.code",
    )
    def _compute_data_journal_entry(self):
        for line in self:
            move = line.move_id
            line.entry_currency_rate = move.entry_currency_rate
            line.land_plot_id = move.land_plot_id
            line.development_project_id = move.development_project_id
            line.development_phase_id = move.development_phase_id
            line.contract_number = move.contract_number
            line.development_project_code = move.development_project_id.code

    @api.onchange("development_project_id")
    def _onchange_development_project_id(self):
        for line in self:
            line.development_project_code = line.development_project_id.code or False

    @api.onchange('partner_id', 'move_id.paid_by', 'move_id.employee_id')
    def _inverse_partner_id(self):
        super()._inverse_partner_id()

    @api.depends('product_id', 'product_uom_id', 
                 'move_id.invoice_type_id.type', 'move_id.invoice_type_id',
                 'date_from', 'date_to', 'leasing_price_unit', 'area')
    def _compute_price_unit(self):
        leasing_invoice_lines = self.filtered(lambda l: l.move_id.state == 'draft' and l.move_id.invoice_type_id.type == 'leasing')
        result = super(AccountMoveLine, self - leasing_invoice_lines)._compute_price_unit()
        for line in leasing_invoice_lines:
            if line.product_uom_id.leasing_type and 'm2' in line.product_uom_id.leasing_type:
                line.price_unit = line.leasing_price_unit * line.area
            else:
                line.price_unit = line.leasing_price_unit
        return result

    # def _get_leasing_month_data(self, date_from, date_to):
    #     result = []
    #     if date_from and date_to:
    #         for dt in rrule.rrule(rrule.MONTHLY, dtstart=date(date_from.year, date_from.month, 1), until=date_to):
    #             first_dayof_month = dt.date()
    #             last_dayof_month = end_of(first_dayof_month, 'month')
    #             lease_start_date = date_from if dt.month == date_from.month and dt.year == date_from.year else first_dayof_month
    #             lease_end_date = date_to if dt.month == date_to.month and dt.year == date_to.year else last_dayof_month
    #             result.append({
    #                 'first_dayof_month': first_dayof_month,
    #                 'last_dayof_month': last_dayof_month,
    #                 'lease_start_date': lease_start_date,
    #                 'lease_end_date': lease_end_date,
    #                 'leasing_days': abs((lease_end_date - lease_start_date).days) + 1,
    #                 'total_days': abs((last_dayof_month - first_dayof_month).days) + 1,
    #             })
    #     return result
    
    # # VND
    # def _get_vnd_leasing_price_unit(self):
    #     return self.leasing_price_unit
    
    # # VND/m2
    # def _get_vnd_m2_leasing_price_unit(self):
    #     return self.leasing_price_unit * self.area
        
    # # VND/m2/month
    # def _get_vnd_m2m_leasing_price_unit(self):
    #     lst_leasing_amount = []
    #     leasing_data = self._get_leasing_month_data(self.date_from, self.date_to)
    #     for data in leasing_data:
    #         total_days = data.get('total_days', False)
    #         leasing_days = data.get('leasing_days', 0)
    #         if not float_is_zero(total_days, 0):
    #             lst_leasing_amount.append(self.leasing_price_unit * self.area * leasing_days / total_days)
    #     return sum(lst_leasing_amount)
    
    # # VND/month
    # def _get_vnd_m_leasing_price_unit(self):
    #     lst_leasing_amount = []
    #     leasing_data = self._get_leasing_month_data(self.date_from, self.date_to)
    #     for data in leasing_data:
    #         total_days = data.get('total_days', 0)
    #         leasing_days = data.get('leasing_days', 0)
    #         if not float_is_zero(total_days, 0):
    #             lst_leasing_amount.append(self.leasing_price_unit * leasing_days / total_days)
    #     return sum(lst_leasing_amount)
    
    # # VND/m2/year
    # def _get_vnd_m2y_leasing_price_unit(self):
    #     date_from = self.date_from
    #     date_to = self.date_to
    #     lst_leasing_amount = []
    #     for dt in rrule.rrule(rrule.YEARLY, dtstart=date(date_from.year, 1, 1), until=date_to):
    #         first_dayof_year = dt.date()
    #         last_dayof_year = end_of(first_dayof_year, 'year')
    #         lease_start_date = first_dayof_year if first_dayof_year > date_from else date_from
    #         lease_end_date = last_dayof_year if last_dayof_year <= date_to else date_to
    #         if first_dayof_year == lease_start_date and last_dayof_year == lease_end_date:
    #             lst_leasing_amount.append(self.leasing_price_unit * self.area)
    #         else:
    #             leasing_data_bymonth = self._get_leasing_month_data(lease_start_date, lease_end_date)
    #             total_month = 0
    #             total_days = 0
    #             is_fullmonth = True
    #             for month in leasing_data_bymonth:
    #                 total_month += 1
    #                 total_days += month.get('leasing_days', 0)
    #                 if month.get('leasing_days', 0) != month.get('total_days', 0):
    #                     is_fullmonth = False
    #             if is_fullmonth:
    #                 lst_leasing_amount.append(self.leasing_price_unit * self.area * total_month / 12)
    #             else:
    #                 total_daysof_year = abs((last_dayof_year - first_dayof_year).days) + 1
    #                 lst_leasing_amount.append(self.leasing_price_unit * self.area * total_days/ total_daysof_year)
    #     return sum(lst_leasing_amount)

    def _generate_report_payment_request(self):
        self.ensure_one()
        price_unit = self.leasing_price_unit if self.leasing_price_unit > 0 else self.price_unit
        digits = self.currency_id.decimal_places if self.currency_id else 0

        return {
            'line_no': self.line_no,
            'index': self.line_no,
            'name': self.name,
            'uom': self.product_uom_id.name,
            'area': formatLang(self.env, self.area, digits=2),
            'price_unit': formatLang(self.env, price_unit, digits=2) if price_unit > 0 else '',
            'quantity': formatLang(self.env, self.quantity, digits=digits),
            'subtotal': formatLang(self.env, float_round(self.price_subtotal, digits), digits=digits),
            'price_total':  formatLang(self.env, float_round(self.price_total, digits), digits=digits),
            'tax_excluded': formatLang(self.env, float_round(self.tax_excluded, digits), digits=digits) if self.tax_excluded else '',
            'tax_rate': formatLang(self.env, self.tax_ids[:1].amount, digits=0),
            'tax_amount': formatLang(self.env, float_round(self.price_subtotal * self.tax_ids[:1].amount / 100, digits), digits=digits) if self.tax_ids[:1].amount else '',
            'connection_quantity': formatLang(self.env, self.connection_quantity, digits),
            'connection_rate': f"{formatLang(self.env, self.connection_rate, digits)}%",
        }

    def write(self, vals):
        if 'partner_id' in vals and self.env.context.get('skip_change_partner'):
            vals.pop('partner_id')
        return super().write(vals)

