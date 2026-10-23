from typing import Any
from datetime import date

from .minvoice_api_helper import MInvoiceAPI


class SingularInvoiceDataInTrans:
    def __call__(self, minvoice):
        action = minvoice.minvoice_action
        if action == "save":
            return self.prepare_save_invoice_data(minvoice)
        elif action == 'publish':
            if minvoice.move_id.minvoice_state != 'uncreated':
                return {
                    "hoadon68_id": minvoice.move_id.minvoice_index
                }
            return self.prepare_save_invoice_data(minvoice)
        elif action == 'adjust':
            return self.prepare_adjust_invoice_data(minvoice)
        elif action == 'replace':
            return self.prepare_replace_invoice_data(minvoice)
        elif action == "cancel":
            return self.prepapre_cancel_invoice_data(minvoice)

        raise ValueError(f"Unknown action: {action}")

    @classmethod
    def _common_invoice_data(cls, minvoice):
        general_invoice_info_data = cls.process_general_invoice_info_data(
            minvoice)
        buyer_info_data = cls.process_buyer_info_data(minvoice)
        seller_info_data = cls.process_seller_info_data(minvoice)
        payments_data = cls.process_payments_data(minvoice)
        item_info_data = cls.process_item_info_data(minvoice)
        summerize_info_data = cls.process_summerize_info_data(minvoice)
        extra_info_data = cls.process_extra_info_data(minvoice)

        result = {
            **general_invoice_info_data,
            **buyer_info_data,
            **seller_info_data,
            **payments_data,
            **summerize_info_data,
            **extra_info_data,
            'details': [item_info_data],
        }

        return result

    @classmethod
    def process_general_invoice_info_data(cls, minvoice):
        move = minvoice.move_id
        digits= move.currency_id.decimal_places if move.currency_id else 0
        info_data = {
            'inv_invoiceIssuedDate': minvoice.minvoice_issued_date.strftime('%Y-%m-%d'),
            'inv_invoiceSeries': minvoice.minvoice_template_id.invoice_series,
            'inv_currencyCode': move.currency_id.name,
            'inv_exchangeRate': move.entry_currency_rate if move.entry_currency_rate > 1 else '',
            'so_benh_an': move.name,
            'ma_dong_ho': move.metering_point,
            'inv_TotalAmountWithoutVat': round(move.amount_untaxed, digits),
            'inv_vatAmount': move.amount_tax,
            'inv_TotalAmount': round(move.amount_total, digits),
        }
        if minvoice.minvoice_action in ("save", "publish") and move.minvoice_state == 'created':
            if move.minvoice_state == 'created':
                info_data.update({
                    'inv_InvoiceAuth_id': move.minvoice_index
                })
            if move.minvoice_no:
                info_data['inv_invoiceNumber'] = move.minvoice_no

        if minvoice.minvoice_action == "publish" and move.minvoice_transaction_id:
            info_data['key_api'] = move.minvoice_transaction_id

        return info_data

    @classmethod
    def process_buyer_info_data(cls, minvoice):
        account_move = minvoice.move_id
        partner = account_move.partner_id
        buyer_info = {
            "inv_buyerAddressLine": partner.get_full_partner_address(),
            "inv_buyerEmail": partner.email or "",
        }
        if partner.company_type == "person":
            buyer_info["inv_buyerDisplayName"] = partner.name
        if partner.company_type == "company" or partner.vat:
            buyer_info["inv_buyerLegalName"] = partner.name
            buyer_info["inv_buyerTaxCode"] = partner.vat or ""
        return buyer_info

    @classmethod
    def process_seller_info_data(cls, minvoice):
        return {}

    @classmethod
    def process_payments_data(cls, minvoice):
        payment_method = minvoice.get_selection_label(
            'minvoice_template_payment_method', minvoice.minvoice_template_payment_method)
        return {'inv_paymentMethodName': payment_method or 'Chuyển khoản'}

    @classmethod
    def process_item_info_data(cls, minvoice):
        item_infos = minvoice._prepare_minvoice_items_vals()
        return {
            'data': item_infos
        }

    @classmethod
    def process_summerize_info_data(cls, minvoice):
        move = minvoice.move_id
        items = move.lines_to_publish_minvoice()
        amount_discount = sum(
            line.price_unit * (line.discount / 100) * line.quantity for line in items)
        amount_total = sum(items.mapped('price_total'))
        amount_untaxed = sum(items.mapped('price_subtotal'))
        return {
            'inv_discountAmount': amount_discount,
        }

    @classmethod
    def process_extra_info_data(cls, minvoice):
        data = minvoice._prepare_minvoice_extra_vals()
        return data

    @classmethod
    def prepare_save_invoice_data(cls, minvoice):
        return {
            'editmode': 1 if minvoice.move_id.minvoice_state == 'uncreated' else 2,
            'data': [cls._common_invoice_data(minvoice)]
        }

    @classmethod
    def prepare_adjust_invoice_data(cls, minvoice):
        original_invoice = minvoice.original_invoice_id
        general_invoice_info_data = cls.process_general_invoice_info_data(
            minvoice)
        buyer_info_data = cls.process_buyer_info_data(minvoice)
        seller_info_data = cls.process_seller_info_data(minvoice)
        payments_data = cls.process_payments_data(minvoice)
        item_info_data = cls.process_item_info_data(minvoice)
        summerize_info_data = cls.process_summerize_info_data(minvoice)
        return {
            **general_invoice_info_data,
            'inv_InvoiceAuth_id': original_invoice.minvoice_index,
            'inv_invoiceIssuedDate': minvoice.minvoice_issued_date.strftime('%Y-%m-%d'),
            **buyer_info_data,
            **seller_info_data,
            **payments_data,
            **summerize_info_data,
            **item_info_data
        }

    @classmethod
    def prepare_replace_invoice_data(cls, minvoice):
        data = cls._common_invoice_data(minvoice)
        original_invoice = minvoice.original_invoice_id
        data.update({
            "inv_originalId": original_invoice.minvoice_index,
            "ghi_chu": minvoice.minvoice_note,
        })
        return {
            'data': [data]
        }

    @classmethod
    def prepapre_cancel_invoice_data(cls, minvoice):
        cancel_date = minvoice.agreement_date or date.today()
        data = {
            "inv_InvoiceAuth_id": minvoice.move_id.minvoice_index,
            "ngayvb": cancel_date.strftime('%Y-%m-%d'),
            "ghi_chu": minvoice.cancel_reason
        }
        return data


class MInvoiceCaller:
    transform_invoice = SingularInvoiceDataInTrans()
    api: Any = None
    minvoice: Any = None

    def __init__(self, minvoice_account, minvoices):
        self.api = MInvoiceAPI(minvoice_account)
        self.minvoices = minvoices

    def prepare(self):
        for minvoice in self.minvoices:
            minvoice = self.transform_invoice(minvoice)
            yield minvoice
