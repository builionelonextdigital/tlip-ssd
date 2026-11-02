---
id: <PREFIX-NUM>            # VD: O2C-14 (tên thư mục)
code: <Mã gốc>              # VD: O2C No. 14
title: <Tên hạng mục>
status: Draft               # Draft → In Review → Approved → Implementing → Done | Dropped
ai_level: <Cao|Trung bình|Thấp>
shared_modules: <Có|Không>
source: <Tracker dòng ... / tài liệu ... mục ...>
business_approver:          # FC ghi tên + ngày khi duyệt. AI KHÔNG điền.
technical_approver:         # TC ghi tên + ngày khi duyệt. AI KHÔNG điền.
---

# <Mã gốc> – <Tên hạng mục>

## 1. Bối cảnh / Hiện trạng

<Hiện hệ thống đang làm gì, vì sao chưa đúng. Trích từ tracker/tài liệu, ghi nguồn.>

## 2. Mục tiêu

<1–3 câu: sau khi xong, người dùng làm được gì.>

## 3. Ngoài phạm vi

- <Những gì KHÔNG làm trong hạng mục này>

## 4. Người dùng và quyền

| Vai trò (group) | Được làm | Không được làm |
|---|---|---|
| <Kế toán viên> | | |

## 5. Yêu cầu nghiệp vụ

- **R1.** <Hệ thống phải ...>
- **R2.** ...

## 6. Tiêu chí nghiệm thu (AC)

Mỗi AC là một kịch bản kiểm tra được, có số liệu cụ thể (dữ liệu giả). Mỗi AC sẽ có ít nhất một test.

| AC | Cho trước (Given) | Khi (When) | Thì (Then) | Ánh xạ R |
|---|---|---|---|---|
| AC1 | <Khách Alpha có RFP 100.000.000 đ chưa post> | <Xác nhận payment 100.000.000 đ> | <RFP được post, đối soát đủ> | R1 |
| AC2 | | | | |

Trường hợp biên bắt buộc xem xét: multi-company, quyền (user không có group), chứng từ đã duyệt/đã post, làm tròn tiền, tiền tệ khác, dữ liệu rỗng.

## 7. Dữ liệu và màn hình bị ảnh hưởng

| Model | Field | Mới / Sửa / Đọc | Ghi chú |
|---|---|---|---|
| `account.move` | `x_field` (mới) | Mới | |

Màn hình / báo cáo: <form, list, wizard, báo cáo nào>

## 8. Ràng buộc

- Tuân thủ `AGENTS.md`.
- <Ràng buộc riêng: không đổi tên field cũ, dữ liệu migration, hiệu năng...>

## 9. Câu hỏi mở

Spec **không được Approved** khi còn câu hỏi chưa trả lời.

| # | Câu hỏi | Người trả lời | Trả lời |
|---|---|---|---|
| Q1 | | FC | |

## 10. Lịch sử

| Ngày | Người | Thay đổi |
|---|---|---|
| <YYYY-MM-DD> | <AI / tên> | Tạo bản nháp |
