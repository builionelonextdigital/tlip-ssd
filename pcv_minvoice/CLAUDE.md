# pcv_minvoice – lưu ý cho AI

**Module dùng chung, tích hợp hệ thống ngoài (M-invoice).** Mức dùng AI: **Thấp** cho phần gọi API.

- **Không bao giờ** đọc, in, log hay đưa vào prompt: mật khẩu, token, `production_host` trong `minvoice.account`.
- **Không gọi API thật** trong test hay khi thử nghiệm. Mock hàm trong `utils/minvoice_api_helper.py` bằng `unittest.mock.patch`.
- Lỗi trong báo cáo audit (#1 đang được sửa dở, chưa commit – kiểm tra `git diff pcv_minvoice` trước): #1 secret mọi user đọc được; #2 phát hành 2 lần; #4 không timeout; #14 credit note gửi số dương; #15 mã thuế sai cho KCT/0%; #16 tổng header lệch dòng; #17 (ở `tlip_account`) hóa đơn đã phát hành vẫn reset draft được.
- Hạng mục liên quan: O2C No. 11 (tạo hóa đơn nháp M-invoice khi submit, nút Update M-Invoice). Điều kiện: M-invoice cho phép cập nhật hóa đơn nháp qua API, **chưa được xác nhận**.
- Mọi luồng phát hành phải idempotent: lưu id giao dịch trước khi gọi, khóa bản ghi chống bấm 2 lần.
- Số tiền gửi đi tính từ các dòng đã làm tròn; quy tắc làm tròn của TLIP là round globally (họp 22/10).
