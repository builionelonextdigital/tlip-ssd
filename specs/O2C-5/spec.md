---
id: O2C-5
code: O2C No. 5
title: Căn lề và cân đối mẫu PDF RFP
status: Draft
ai_level: Trung bình
shared_modules: Không
source: GitHub Issue #18 (từ TLIP_Phase_Tracker.xlsx, docx giải pháp O2C mục No. 5); khảo sát code tlip_base, tlip_account
business_approver:
technical_approver:
---

# O2C No. 5 – Căn lề và cân đối mẫu PDF RFP

## 1. Bối cảnh / Hiện trạng

- TLIP phản ánh mẫu PDF RFP (Yêu cầu thanh toán) có lề quá sát mép giấy, trang in chưa cân đối. *(Issue #18)*
- Khảo sát code: 11 mẫu in RFP trong `tlip_account/report/ir_actions_report.xml` (MF-RQ, Power 1, Power 2, Power 2.1, Power 2.2, Power 3, Power 4, Water, Other Turnover, Other Request, Land Rent) dùng chung khổ giấy `tlip_base.tlip_paper_format`.
- Khổ giấy này đang đặt **lề trái = 0 mm, lề phải = 0 mm, lề dưới = 5 mm**, lề trên = 25 mm, header_spacing = 20, dpi = 140. Lề trái/phải bằng 0 là nguyên nhân chính khiến nội dung sát mép giấy.
- Bản ghi khổ giấy nằm trong `<data noupdate="1">`: sửa XML **không** tự áp dụng khi nâng cấp module trên database đang chạy; cần script migration.

## 2. Mục tiêu

Mọi mẫu PDF RFP in ra trên A4 có lề đều hai bên, không bị cắt chữ, cân đối giữa các khối; chỉnh một lần áp dụng cho tất cả Request Type.

## 3. Ngoài phạm vi

- Thay đổi nội dung, câu chữ, bố cục chi tiết bên trong từng mẫu (chờ mẫu chuẩn từ TLIP – Q2).
- Mẫu in Payment (`paperformat_account_payment`) và Batch Payment (`base.paperformat_euro`): không đổi.
- Lỗi tên file in của mẫu Power 1 (`print_report_name` đang là `'Power 2 - %s'`): ghi nhận, tách thành task riêng.

## 4. Người dùng và quyền

| Vai trò | Được làm | Không được làm |
|---|---|---|
| Người tạo / in RFP (kế toán, sales) | In PDF RFP như hiện tại | — (không đổi quyền) |
| Quản trị hệ thống | Sửa khổ giấy trong Settings › Technical › Paper Format | — |

## 5. Yêu cầu nghiệp vụ

- **R1.** Khổ giấy dùng chung của RFP có lề trái và lề phải bằng nhau, đủ rộng để không sát mép giấy (giá trị đề xuất: 15 mm – Q1).
- **R2.** Lề dưới đủ để nội dung trang cuối không sát mép (đề xuất 15 mm – Q1); lề trên và khoảng cách header giữ nguyên để không đổi vị trí logo.
- **R3.** Thay đổi áp dụng cho cả 11 mẫu RFP và cho database đang chạy sau khi nâng cấp module (không chỉ cài mới).
- **R4.** Không ảnh hưởng mẫu Payment và Batch Payment.

## 6. Tiêu chí nghiệm thu (AC)

| AC | Cho trước (Given) | Khi (When) | Thì (Then) | R |
|---|---|---|---|---|
| AC1 | Module đã cài/nâng cấp | Đọc khổ giấy `tlip_base.tlip_paper_format` | A4, dọc; lề trái = lề phải = 15 mm; lề dưới = 15 mm; lề trên = 25 mm; header_spacing = 20 | R1, R2 |
| AC2 | 11 mẫu in RFP của `tlip_account` | Kiểm tra khổ giấy từng mẫu | Cả 11 mẫu dùng `tlip_base.tlip_paper_format` | R3 |
| AC3 | Database đang chạy có khổ giấy với lề trái/phải = 0 | Nâng cấp module `tlip_base` | Khổ giấy được cập nhật theo AC1 | R3 |
| AC4 | Mẫu Payment và Batch Payment | Kiểm tra khổ giấy | Vẫn là `tlip_account.paperformat_account_payment` và `base.paperformat_euro`, giá trị không đổi | R4 |
| AC5 | RFP MF-RQ của khách "Alpha" (dữ liệu giả, 1 trang) | In PDF trên môi trường test | Nội dung cách mép trái và phải đều nhau, không chữ nào bị cắt; logo và tiêu đề giữ vị trí như cũ | R1, R2 |
| AC6 | RFP Water nhiều dòng (dữ liệu giả, ≥ 2 trang) | In PDF | Trang 2 có lề như trang 1, dòng cuối không sát mép dưới | R2 |

## 7. Dữ liệu và màn hình bị ảnh hưởng

| Model / bản ghi | Field | Mới / Sửa / Đọc | Ghi chú |
|---|---|---|---|
| `report.paperformat` – `tlip_base.tlip_paper_format` | `margin_left`, `margin_right`, `margin_bottom` | Sửa | Bản ghi `noupdate` → cần migration |
| `ir.actions.report` – 11 mẫu RFP | `paperformat_id` | Đọc | Không đổi |
| `invoice.type` | `report_payment_request_id` | Đọc | Giữ mẫu đang dùng (Issue #18) |

Màn hình: bản in PDF RFP (nút Print trên RFP / Payment request).

## 8. Ràng buộc

- Tuân thủ `AGENTS.md`. Không đổi tên bản ghi khổ giấy (tên hiện có lỗi chính tả "Foramt" – giữ nguyên, ngoài phạm vi).
- Thay đổi ở `tlip_base` (module nền, không thuộc nhóm module dùng chung của `sdd.config.yml`); kiểm tra lại các mẫu khác dùng `tlip_base.tlip_layout`.

## 9. Câu hỏi mở

| # | Câu hỏi | Người trả lời | Trả lời |
|---|---|---|---|
| Q1 | Giá trị lề mong muốn? Đề xuất: trái 15 mm, phải 15 mm, dưới 15 mm, trên giữ 25 mm. TLIP có quy chuẩn văn bản khác (VD: trái 30 mm, phải 15 mm theo Nghị định 30/2020 về văn bản hành chính) không? | FC (xác nhận với TLIP) | |
| Q2 | Issue ghi "Cần TLIP gửi mẫu hoặc xác nhận các căn chỉnh mong muốn". TLIP đã gửi mẫu chưa? Nếu chưa: bản này chỉ chỉnh lề (R1–R4), phần khoảng cách giữa các khối (đầu trang, bảng chi tiết, thông tin chuyển khoản, chữ ký) làm khi có mẫu – đồng ý? | FC | |
| Q3 | Mẫu nào là mẫu TLIP thấy lệch nhất để QC ưu tiên test (MF-RQ, Water, Land Rent…)? | FC | |

## 10. Lịch sử

| Ngày | Người | Thay đổi |
|---|---|---|
| 2026-11-02 | AI (/sdd-spec) | Tạo bản nháp từ Issue #18 và khảo sát code |
