---
id: <PREFIX-NUM>
---

# Tasks – <Mã gốc>

Quy ước: `[ ]` chưa làm · `[x]` xong · `[~]` đang làm · `[-]` bỏ (ghi lý do).
Cột **Ai**: `AI` hoặc `TC`. Với mức dùng AI = Thấp, logic lõi luôn là `TC`.
Mỗi task nhỏ, kiểm tra được, ghi rõ file.

## 1. Test (viết trước, phải FAIL)

- [ ] T1 · AI · Tạo `module/tests/__init__.py`, `test_<name>.py` (khung, setUpClass dữ liệu giả)
- [ ] T2 · AI · Test AC1 → `test_ac1_...`
- [ ] T3 · AI · Chạy test, xác nhận FAIL đúng lý do (chưa có chức năng)

## 2. Model / field

- [ ] T4 · AI · ...

## 3. Logic

- [ ] T5 · <AI|TC> · ...

## 4. View

- [ ] T6 · AI · ...

## 5. Bảo mật

- [ ] T7 · AI · ACL có group, record rule theo công ty

## 6. Data, bản dịch, version, migration

- [ ] T8 · AI · `i18n/vi_VN.po`
- [ ] T9 · AI · Tăng version manifest
- [ ] T10 · AI · Migration (nếu plan yêu cầu)

## 7. Kiểm tra

- [ ] T11 · AI · Chạy test module → PASS
- [ ] T12 · AI · Chạy test module phụ thuộc (nếu đụng module dùng chung)
- [ ] T13 · AI · `/sdd-verify`
