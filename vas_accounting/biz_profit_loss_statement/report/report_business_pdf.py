# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, models


class RevenueReportPdf(models.AbstractModel):
    _name = "report.biz_profit_loss_statement.report_business_pdf"
    _description = "Business Activities Results PDF"

    def get_lines(self, record):
        lines = []
        for line in record.business_activities_results_line_ids:
            lines.append({
                "chi_tieu": line.target_config_id.targets_name,
                "ma_so": line.code or "",
                "thuyet_minh": line.present or "",
                "nam_nay": self.format_float_number(line.this_year),
                "nam_truoc": self.format_float_number(line.year_ago),
            })
        return lines

    def format_float_number(self, num):
        if not num:
            return "0"

        number = float(num)
        if number % 1 == 0:
            return "{:,.0f}".format(number)
        return "{:,.2f}".format(number).rstrip("0")

    def get_company_address(self, company):
        address = ""
        if company:
            if company.street:
                address += company.street
            if company.street2:
                address += len(address) > 0 and ", " + company.street2 or company.street2
            if company.city:
                address += len(address) > 0 and ", " + company.city or company.city
            if company.state_id:
                address += len(address) > 0 and ", " + company.state_id.name or company.state_id.name
            if company.country_id:
                address += len(address) > 0 and ", " + company.country_id.name or company.country_id.name
        return address

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["business.activities.results"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "business.activities.results",
            "docs": docs,
            "date_now": datetime.today(),
            "get_lines": self.get_lines,
            "get_company_address": self.get_company_address,
        }
