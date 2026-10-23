import json
from odoo import api, fields, models, _
from datetime import datetime, timedelta


class ReportAccountingBalanceSheet(models.AbstractModel):
    _name = 'report.biz_accounting_balance_sheet.rp_account_balance_pdf'


    # def get_number_remove_zero(self, number):
    #     if number % 1 == 0:
    #         return int(number)
    #     else:
    #         return number

    def format_float_number(self, offer, number):
        if not offer.apply_by and not offer.code:
            number_format = None
        else:
            if number >= 0:
                if number % 1 == 0:
                    number_format = "{:,.0f}".format(number)
                else:
                    number_format = "{:,.2f}".format(number)
            else:
                number = abs(number)
                if number % 1 == 0:
                    number_format = "(" + "{:,.0f}".format(number) + ")"
                else:
                    number_format = "(" + "{:,.2f}".format(number) + ")"
        return number_format

    def get_company_address(self, company):
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


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['accounting.balance.sheet.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'accounting.balance.sheet.report',
            'docs': docs,
            'format_float_number': self.format_float_number,
            'get_company_address': self.get_company_address
        }