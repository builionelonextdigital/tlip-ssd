# tlip_account – lưu ý cho AI

Module lớn nhất, chứa phần lớn hạng mục O2C và Kế toán. Nhiều hạng mục ở đây có **Mức dùng AI = Thấp**.

## Mô hình chính

- RFP: `account.move` với `is_request_payment = True`; loại yêu cầu `invoice_type_id` → model `invoice.type` (24 loại, mỗi loại gắn sản phẩm, tài khoản, mẫu in, sequence).
- Payment: `account.payment` (có luồng duyệt riêng); Batch: `batch.payment` (model riêng của TLIP).
- Ngân sách: `budget.line`, `budget.allocation.approval`, `budget.reserved`, Budget Code trên `account.analytic.account`.
- Khóa sổ kỳ: `accounting.period.closing`.

## Quy tắc kế toán AI phải giữ

- Chứng từ đã post hoặc đã phát hành M-invoice: không sửa số tiền, đối tác, dòng; điều chỉnh bằng credit note / hóa đơn điều chỉnh.
- Mọi truy vấn số liệu: chỉ dòng `parent_state = 'posted'` (trừ khi tài liệu nói khác) và lọc `company_id`.
- Tiền: dùng `currency.round`, `compare_amounts`, `is_zero`. Không so float, không chia cho tỷ giá có thể bằng 0.
- Không phá kiểm tra khóa sổ: context `bypass_period_closing`, `force_post` chỉ hợp lệ với kế toán trưởng (AUDIT #19, #20).
- Ngày hạch toán (`date`) khác ngày hóa đơn (`invoice_date`) và ngày ký/phát hành: không gộp làm một (O2C No. 11).

## Hạng mục Mức Thấp – AI không viết logic lõi

O2C No. 9 (phân bổ FIFO), No. 11 (kỳ chốt điện nước + M-invoice), No. 13 (Deferred Revenue 3387 – **chưa chốt** thời điểm tạo bảng phân bổ); Kế toán: tỷ giá bình quân, thuế gross/net, chi phí trích trước 335, báo cáo dòng tiền theo budget, lưu tỷ giá bảo hiểm.
Với các hạng mục này: giải thích code cũ, viết test theo ví dụ số liệu của FC, lập kế hoạch; TC viết phần lõi.

## Lỗi audit trong module

#19 đang được sửa dở trong `_post` (chưa commit) – kiểm tra `git diff tlip_account` trước.

#12 báo cáo đối chiếu ngân hàng, #13 hạn thanh toán ngày làm việc, #17 reset draft hóa đơn đã phát hành, #18 ACL quá rộng, #19 context bypass, #20 kỳ tương lai, #21–22 điều chuyển ngân sách.
