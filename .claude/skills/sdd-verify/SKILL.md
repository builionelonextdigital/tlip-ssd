---
name: sdd-verify
description: Bước 5 của quy trình SDD – kiểm tra một hạng mục Odoo trước khi mở merge request – đối chiếu từng tiêu chí nghiệm thu trong spec với test, diff với plan, checklist AGENTS.md, chạy test và soạn mô tả MR. Dùng khi người dùng nói "/sdd-verify <ID>", "kiểm tra trước MR", hoặc khi mọi task trong tasks.md đã xong.
---

# /sdd-verify – Kiểm tra và soạn mô tả MR

Chỉ đọc và chạy test. **Không sửa code** trong bước này; phát hiện lỗi thì báo và đề xuất quay lại `/sdd-implement`.

## 1. Thu thập

- `specs/<ID>/spec.md`, `plan.md`, `tasks.md`, `sdd.config.yml`, `AGENTS.md`.
- Diff: `git diff <nhánh gốc>...HEAD` (hỏi người dùng nhánh gốc nếu không rõ; mặc định `main`).

## 2. Kiểm tra

| # | Kiểm tra | Cách |
|---|---|---|
| V1 | Mọi task `[x]` hoặc `[-]` có lý do | Đọc tasks.md |
| V2 | Mỗi AC có ≥ 1 test, test kiểm tra đúng Then của AC | Grep `test_ac<n>_`, đọc assert |
| V3 | Test chạy qua | `test_command` cho từng module trong plan; thêm module phụ thuộc nếu đụng module dùng chung |
| V4 | Diff không vượt phạm vi plan | File/module thay đổi ⊆ plan mục 2–3; ghi rõ file lạ |
| V5 | Không đụng `third_party_modules` | Diff |
| V6 | Quy ước Odoo 18 & bảo mật trong `AGENTS.md` | ACL có group, record rule công ty, không f-string SQL, `compare_amounts`, timeout HTTP, `sudo()` có comment, view `<list>` |
| V7 | Version manifest tăng; migration nếu plan yêu cầu | Diff `__manifest__.py`, `migrations/` |
| V8 | Bản dịch vi_VN cho chuỗi mới | Diff `i18n/` |
| V9 | Mức dùng AI được tôn trọng | ai_level Thấp → logic lõi phải do TC viết (hỏi người dùng xác nhận) |

## 3. Kết quả

1. Bảng V1–V9: Đạt / Không đạt / Không áp dụng + ghi chú (file, hàm).
2. Bảng ánh xạ **AC → test → kết quả**.
3. Nếu tất cả đạt: đề nghị TC đổi spec sang `status: Done` sau khi merge (AI không tự đổi).
4. Mô tả MR:

```
[<Mã gốc>] <Tên hạng mục>

Spec: specs/<ID>/spec.md   Plan: specs/<ID>/plan.md
Giải pháp: <1–2 câu>
Module: <...>   Module dùng chung: Có/Không (Có → cần pod Core review)
Field mới/sửa: <model.field>
AC → test: AC1 ✔ test_ac1_..., AC2 ✔ ...
Test: <số test chạy / qua, các module đã chạy>
Mức dùng AI: <...>; phần AI viết: <...>; phần TC viết: <...>
Cần FC/khách hàng xác nhận (UAT): <...>
```
