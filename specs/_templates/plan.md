---
id: <PREFIX-NUM>
spec_status_at_plan: Approved
status: Draft               # Draft → Approved (TC duyệt)
technical_approver:         # TC ghi tên + ngày. AI KHÔNG điền.
---

# Plan kỹ thuật – <Mã gốc>

## 1. Tóm tắt cách làm

<3–6 câu. Giải pháp kỹ thuật tổng thể.>

## 2. Hiện trạng code (đã khảo sát)

| File | Hàm / phần tử | Vai trò hiện tại | Sẽ thay đổi gì |
|---|---|---|---|
| `module/models/x.py` | `_compute_y` | | |

## 3. Module bị ảnh hưởng

| Module | Loại thay đổi | Dùng chung? | Module phụ thuộc cần chạy test |
|---|---|---|---|
| | | Có/Không | |

Nếu có module dùng chung: cần review pod Core (ghi vào mô tả MR).

## 4. Thiết kế

### 4.1 Model / field

| Model | Field | Kiểu | Thuộc tính (store, compute, company_dependent, groups...) |
|---|---|---|---|

### 4.2 Logic

<Hàm nào mới/sửa, thuật toán, thứ tự gọi `super()`, khóa dòng nếu có đồng thời.>

### 4.3 View

<Form/list/search, dùng `<list>`, `invisible=`/`readonly=` (Odoo 18).>

### 4.4 Bảo mật

- ACL (`ir.model.access.csv`) – luôn có group:
- Record rule (có điều kiện công ty):
- `sudo()` (nếu có, lý do + giới hạn):

### 4.5 Dữ liệu & migration

- Version manifest: `18.0.x.y.z` → `18.0.x.y.z+1`
- Script `migrations/`: <có/không, làm gì>
- Data XML (cron, sequence, `noupdate`):

### 4.6 Bản dịch

- Chuỗi mới cần thêm vào `i18n/vi_VN.po`.

## 5. Chiến lược test

| AC | File test | Tên test | Loại (nghiệp vụ/quyền/multi-company/API mock) |
|---|---|---|---|
| AC1 | `module/tests/test_x.py` | `test_ac1_...` | Nghiệp vụ |

## 6. Phân chia theo mức dùng AI

| Phần | Ai viết | Ghi chú |
|---|---|---|
| Test | AI | |
| Field, view, security | AI | |
| Logic lõi | <AI / TC> | Bắt buộc TC nếu mức Thấp |

## 7. Rủi ro

| Rủi ro | Ảnh hưởng | Cách giảm |
|---|---|---|

## 8. Kiểm tra theo AGENTS.md

- [ ] Multi-company: `_check_company_auto`, `check_company=True`, truy vấn lọc công ty
- [ ] Tiền: `compare_amounts` / `is_zero`
- [ ] SQL tham số hóa, không f-string
- [ ] HTTP ra ngoài có timeout
- [ ] Không đổi tên/xóa field đang có
- [ ] Không sửa module bên thứ ba
