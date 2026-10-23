# -*- coding: utf-8 -*-
from odoo import api, models
from datetime import datetime

class rp_detail_book_pdf(models.AbstractModel):
    _name = 'report.biz_details_of_account_books.rp_detail_book_pdf'
    _description = 'rp_detail_book_pdf'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        doc = self.env['detail.book.account'].browse(docids)
        options = data or {}
       
        from_date = options.get('date', {}).get('date_from', '')
        to_date = options.get('date', {}).get('date_to', '')
        
        if from_date:
            from_date_date = datetime.strptime(from_date, "%Y-%m-%d")
            from_date = from_date_date.strftime('%d/%m/%Y')
        if to_date:
            to_date_date = datetime.strptime(to_date, "%Y-%m-%d")
            to_date = to_date_date.strftime('%d/%m/%Y')
        
        sub_title = 'Từ ngày %s đến ngày %s' % (from_date, to_date)

        # --- ĐÂY LÀ ĐOẠN TỐI ƯU HÓA HIỆU NĂNG ---
        # Kiểm tra nếu data truyền sang là dữ liệu đã được tính toán từ trước
        if options.get('is_precomputed'):
            return {
                'doc_ids': docids,
                'doc': doc,
                'get_company_address': doc.get_company_address,
                'sub_title': sub_title,
                'get_accounts': options.get('precomputed_account_name', ''), # Lấy trực tiếp tên TK đã xử lý
                'get_partners': doc._get_partners(options),
                'lines': options.get('precomputed_lines', {}), # Dùng luôn cụm data dict mà không query lại
                'doc_model': 'detail.book.account',
            }

        # --- PHƯƠNG ÁN DỰ PHÒNG (FALLBACK) ---
        # Nếu người dùng không in ZIP mà click nút in PDF thông thường ngoài View giao diện
        report_id = self.env['account.report'].browse(int(options['report_id']))
        print_mode_self = report_id.with_context(no_format=True, print_mode=True, prefetch_fields=False)
        print_options = print_mode_self.get_options(previous_options=options)
        lines = report_id._filter_out_folded_children(print_mode_self._get_lines(print_options))
        
        # Sửa lỗi gọi sai tham số ở code cũ của bạn (gốc: doc.get_format_data_lines(report_id, lines))
        res = doc.get_format_data_lines_pdf(report_id, lines)
        
        return {
            'doc_ids': docids,
            'doc': doc,
            'get_company_address': doc.get_company_address,
            'sub_title': sub_title,
            'get_accounts': doc._get_accounts(options),
            'get_partners': doc._get_partners(options),
            'lines': res,
            'doc_model': 'detail.book.account',
        }