from odoo import api, models
from itertools import groupby


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _prepare_base_line_grouping_key(self, base_line):
        # Add tax_excluded to the grouping key so that lines with different tax_excluded
        grouping_key = super()._prepare_base_line_grouping_key(base_line)
        grouping_key.update({
            "tax_excluded": 0,
            "leasing_price_unit": 0,
            "area": 0,
        })
        return grouping_key

    @api.model
    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
        record = base_line.get('record')
        if record and hasattr(record, 'move_id'):
            invoice_type_rounding = record.move_id.invoice_type_id.tax_calculation_rounding_method
            if invoice_type_rounding:
                rounding_method = invoice_type_rounding
        return super()._add_tax_details_in_base_line(
            base_line, company, rounding_method=rounding_method
        )

    @api.model
    def _add_tax_details_in_base_lines(self, base_lines, company):
        """
        Expected tax_amount = (untaxed_amount + tax_excluded)/100 * tax_rate
        Create a new base line for tax_excluded and add its tax details to the original base line.
        """
        super()._add_tax_details_in_base_lines(base_lines, company)

        for base_line in base_lines:
            if "tax_excluded" not in base_line or not base_line["tax_excluded"]:
                continue
            if not base_line.get("tax_details") or not base_line["tax_details"].get("taxes_data"):
                continue

            new_base_line = self._prepare_tax_excluded_line(base_line)
            self._add_tax_details_in_base_lines([new_base_line], company)
            taxes_data = base_line["tax_details"]["taxes_data"] + new_base_line["tax_details"]["taxes_data"]

            # Re-group by tax to avoid having two lines for the same tax (one from the original line, one from the tax_excluded line)
            new_taxes = []
            for tax, lines in groupby(
                sorted(taxes_data, key=lambda x: x["tax"]),
                key=lambda x: x["tax"],
            ):
                lines = list(lines)
                new_taxes.append(
                    {
                        "tax": tax,
                        "tax_amount": sum(line["tax_amount"] for line in lines),
                        "raw_tax_amount_currency": sum(line["raw_tax_amount_currency"] for line in lines),
                        "raw_tax_amount": sum(line["raw_tax_amount"] for line in lines),
                        **{k: lines[0][k] for k in lines[0] if k not in ("tax_amount", "tax", "raw_tax_amount_currency", "raw_tax_amount")},
                    }
                )

            base_line["tax_details"].update({
                "taxes_data": new_taxes,
            })

    def _prepare_tax_excluded_line(self, base_line):
        new_base_line = base_line.copy()
        new_base_line.pop("tax_excluded")
        new_base_line.update(
            {
                "price_unit": -base_line["tax_excluded"],
                "quantity": 1,
            }
        )
        return new_base_line
