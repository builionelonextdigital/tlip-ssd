---
name: odoo-feature
description: Làm một hạng mục trong tracker TLIP (mã O2C No. x, P2P No. x hoặc hạng mục Kế toán) từ đọc giải pháp, viết test, viết code đến chuẩn bị merge request. Dùng khi TC giao một mã hạng mục hoặc nói "làm hạng mục ...".
---

# Làm một hạng mục trong tracker

## Bước 1. Lấy thông tin hạng mục

Hỏi mã hạng mục nếu người dùng chưa nói. Đọc dòng tương ứng trong tracker:

```bash
python3 - <<'PY'
import openpyxl, sys
code = "O2C No. 1"   # thay bằng mã hạng mục
ws = openpyxl.load_workbook("Project-infomations/TLIP_Phase_Tracker.xlsx", data_only=True)["Chi tiết task"]
head = [c.value for c in ws[4]]
for row in ws.iter_rows(min_row=5, values_only=True):
    if row[head.index("Mã")] == code:
        for h, v in zip(head, row):
            if v: print(f"## {h}\n{v}\n")
PY
```

Các cột cần dùng: **Vấn đề / Hiện trạng**, **Giải pháp**, **Cách làm**, **Model / Field cần sửa**, **Mức dùng AI**, **Ghi chú**.
Tài liệu gốc (docx) nằm trong `Project-infomations/O2C/` và `Project-infomations/07. Deliverables/`. Nếu cần chi tiết hơn tracker, nhờ người dùng dán đoạn liên quan.

Nếu cột Ghi chú báo hạng mục **chưa chốt** (ví dụ O2C No. 13, No. 16) thì dừng lại, báo người dùng điểm cần chốt trước.

## Bước 2. Kiểm tra mức dùng AI

- **Cao / Trung bình**: tiếp tục.
- **Thấp**: chỉ làm Bước 3, 4 và lập kế hoạch code (file, hàm, thứ tự). Không viết logic lõi; để TC viết rồi bạn hỗ trợ review và chạy test.

## Bước 3. Tìm code liên quan

- Tìm model, field, view hiện có bằng grep theo tên model/field trong cột "Model / Field cần sửa".
- Field đánh dấu `(mới)` là field cần tạo; field không đánh dấu là field đã có, không tạo trùng.
- Xác định module chứa model. Nếu là `tlip_approval`, `tlip_access_rights`, `pcv_minvoice`, `pcv_mysign` thì ghi chú cần pod Core review.
- Đọc `CLAUDE.md` của module nếu có.

## Bước 4. Viết test trước

Dùng skill `odoo-test`. Mỗi tiêu chí nghiệm thu (FC cung cấp, hoặc suy ra từ cột Giải pháp và xác nhận lại với người dùng) thành ít nhất một test. Chạy test và xác nhận test **đang fail** vì chưa có chức năng.

## Bước 5. Viết code

Theo thứ tự: model/field → logic → view → security (ACL + record rule) → data (cron, sequence, activity type) → bản dịch vi_VN → tăng version manifest → migration nếu cần.
Tuân thủ mục 3 và 4 trong `AGENTS.md`. Giữ diff nhỏ, không refactor phần không liên quan.

## Bước 6. Kiểm tra

1. Chạy lại test của module, tất cả phải qua.
2. Nếu sửa module dùng chung: chạy thêm test của module phụ thuộc (`tlip_account`, `tlip_procurement`, ...).
3. Cập nhật module trên database test, mở form/list liên quan nếu người dùng yêu cầu kiểm tra giao diện.

## Bước 7. Chuẩn bị merge request

Soạn mô tả theo mẫu, **không tự commit hay push**:

```
[<Mã hạng mục>] <Tên hạng mục>

Giải pháp: <1–2 câu>
Module: <danh sách>   Module dùng chung: Có/Không (nếu Có: cần pod Core review)
Field mới/sửa: <model.field>
Test: <file test, số test, kết quả>
Mức dùng AI: <Cao/Trung bình/Thấp>; phần AI viết: <...>; phần TC tự viết: <...>
Cần FC/TLIP xác nhận: <...>
```
