# Quy định dùng AI khi phát triển dự án TLIP

Áp dụng cho TC, FC và pod Core của A1 / Rikkei. Đi kèm với `AGENTS.md`, `CLAUDE.md` và các skill trong `.claude/skills/`.

## 1. Trước khi bắt đầu

- [ ] TLIP đã được thông báo và đồng ý việc dùng công cụ AI trên mã nguồn của họ (ghi vào biên bản họp tuần).
- [ ] Đã kiểm tra điều khoản bảo mật (NDA) trong hợp đồng và license Odoo Enterprise.
- [ ] Chỉ dùng bản AI doanh nghiệp có cam kết không dùng dữ liệu để huấn luyện. Danh sách công cụ được phép: ............ (PM điền).
- [ ] Mỗi TC đã đọc `AGENTS.md` và file này.

## 2. Dữ liệu tuyệt đối không đưa vào AI

- Dữ liệu thật của TLIP: database staging/production, file export, `cosphi.json`, `electrict.json`, `water.json`.
- Mật khẩu, token: `odoo.conf`, tài khoản M-invoice, MySign, tài khoản truy cập server TLIP.
- Ảnh chụp màn hình hệ thống thật có tên khách hàng, số tiền.

Cần ví dụ thì dùng dữ liệu giả, như ví dụ trong tài liệu giải pháp (khách "Alpha", RFP `RQ-TQ-202608-0009`).

## 3. Mức dùng AI

Theo cột **Mức dùng AI** trong `Project-infomations/TLIP_Phase_Tracker.xlsx`:

| Mức | AI được làm | TC phải làm |
|---|---|---|
| Cao | Sinh code + test | Đọc lại toàn bộ, chạy test, chịu trách nhiệm |
| Trung bình | Khung code, view, security, test | Viết/soát logic nghiệp vụ với FC |
| Thấp | Đọc code cũ, giải thích, viết test theo ví dụ số liệu, lập kế hoạch | Tự viết logic lõi |

## 4. Cổng kiểm soát (giống code tự viết)

1. Test tự động chạy qua.
2. Review chéo trong pod.
3. Pod Core review nếu đụng `tlip_approval`, `tlip_access_rights`, `pcv_minvoice`, `pcv_mysign`.
4. UAT với key user TLIP.

Code do AI sinh không được bỏ qua bất kỳ cổng nào.

## 5. Thí điểm Đợt 1 O2C (No. 23, 14, 1)

Ghi lại cho mỗi hạng mục để quyết định có áp rộng hay không:

| Mã | MD ước lượng | MD thực tế | Mức AI | Phần AI viết (%) | Lỗi phát hiện ở review | Lỗi phát hiện ở UAT | Ghi chú |
|---|---|---|---|---|---|---|---|
| O2C No. 23 | 7 | | Cao | | | | |
| O2C No. 14 | 1,5 | | Trung bình | | | | |
| O2C No. 1 | 8,5 | | Trung bình | | | | |

Tiêu chí áp rộng: MD thực tế thấp hơn ước lượng và số lỗi ở UAT không tăng so với hạng mục làm tay.
