from odoo import models

from dateutil.relativedelta import relativedelta

class MInvoiceActionWizard(models.TransientModel):
    _inherit = 'minvoice.action.wizard'

    def _prepare_minvoice_extra_vals(self):
        result = super()._prepare_minvoice_extra_vals()
        move = self.move_id
        result.update({
            'vi_tri': move.land_plot_id.name or '',
            'doc_tien_e': move.amount_in_words_en or '',
            'tgtttbchu': move.amount_in_words_vn or ''
        })
        if move.invoice_type_id.type == 'leasing':
            invoice_line = move.invoice_line_ids[:1]
            date_from = invoice_line.date_from and invoice_line.date_from.strftime('%Y-%m-%d')
            date_to = invoice_line.date_to and invoice_line.date_to.strftime('%Y-%m-%d')
            result.update({
                'tu_ngay': date_from,
                'den_ngay': date_to
            })
        return result

    def _prepare_minvoice_items_vals(self):
        item_infos = super()._prepare_minvoice_items_vals()

        is_leasing_type = self.move_id.invoice_type_id.type == 'leasing'

        lines = self.move_id.lines_to_publish_minvoice()
        decimal_places = self.move_id.currency_id.decimal_places
        index = 0
        for (item_info, line) in zip(item_infos, lines):
            if line.date_from and line.date_to:
                delta = relativedelta(line.date_to, line.date_from)
                months = delta.years * 12 + delta.months
                # Optionally include fractional months based on days
                if delta.days > 0:
                    days_in_month = (line.date_to - (line.date_to.replace(day=1))).days + 1
                    fractional_month = delta.days / days_in_month
                    months += fractional_month
            else:
                months = 0

            item_info.update({
                'stt_rec0': line.line_no,
                'so_thang': months,
                'dien_tich': line.area if line.area > 0 else '',
                'dvt_eng': f"({line.product_uom_id.uom_invoice_en})" if line.product_uom_id.uom_invoice_en else ''
            })

            if is_leasing_type:
                self._update_leasing_type_line(line, item_info, decimal_places)

            if line.tax_excluded:
                excluded_line_info = {
                    "tchat": 1,
                    "stt_rec0": None,
                    "inv_itemName": "Trong đó: Tiền thuê đất không chịu thuế giá trị gia tăng (In which: Land rent amount not subject to VAT)",
                    "inv_unitCode": line.product_uom_id.name or "",
                    "inv_quantity": None,
                    "inv_unitPrice": None,
                    "inv_TotalAmountWithoutVat": round(line.tax_excluded, decimal_places),
                    "ma_thue": "0",
                    "inv_vatAmount": 0,
                    "inv_TotalAmount": round(line.tax_excluded, decimal_places),
                }
                item_infos.insert(index, excluded_line_info)
                index += 1

            index += 1

        return item_infos

    def _update_leasing_type_line(self, line, item_info, decimal_places):
        qty = line.quantity
        price_unit = abs(line.leasing_price_unit) if line.leasing_price_unit > 0 else abs(line.price_unit)
        discount_amount = price_unit * (line.discount / 100) * qty

        item_info.update({
            "inv_unitPrice": '' if line.quantity < 1 else price_unit,
            "inv_quantity": '' if line.quantity < 1 else line.quantity,
            "inv_discountAmount": discount_amount,
            "inv_TotalAmountWithoutVat": round(price_unit if line.quantity < 1 else line.price_subtotal, decimal_places),
        })

        if self.minvoice_action == "create" and line.move_id.move_type == 'out_refund':
            item_info.update({
                'inv_unitPrice': item_info['inv_unitPrice'] * -1,
                'inv_TotalAmountWithoutVat': round(item_info['inv_TotalAmountWithoutVat'] * -1, decimal_places),
            })
