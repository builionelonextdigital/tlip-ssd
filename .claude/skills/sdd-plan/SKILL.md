---
name: sdd-plan
description: Bước 2 của quy trình SDD – từ specs/<ID>/spec.md đã Approved, khảo sát code Odoo 18 và viết specs/<ID>/plan.md (module, model/field, logic, view, bảo mật, migration, chiến lược test, phân chia AI/TC). Dùng khi người dùng nói "/sdd-plan <ID>", "lập plan kỹ thuật" cho một hạng mục đã có spec.
---

# /sdd-plan – Lập plan kỹ thuật

## 0. Cổng kiểm tra (bắt buộc)

1. Đọc `sdd.config.yml`, `AGENTS.md`, `specs/<ID>/spec.md`.
2. Spec phải có `status: Approved` **và** có `business_approver`, `technical_approver`. Nếu không → **dừng**, báo người dùng còn thiếu gì.
3. Mục "Câu hỏi mở" của spec không còn dòng nào trống cột "Trả lời". Còn → dừng, liệt kê.

## 1. Khảo sát code

- Tìm mọi model/field/view trong mục 7 của spec: `grep -rn "_name = '<model>'\|_inherit = '<model>'" --include=*.py`.
- Đọc hàm sẽ bị ảnh hưởng (override `create`, `write`, `action_post`, compute...). Ghi file và tên hàm vào mục 2 của plan, **không ghi số dòng** (dễ lệch).
- Xác định model kế thừa mixin dùng chung, record rule đang áp dụng, module phụ thuộc (`depends` trong manifest).
- Đọc `CLAUDE.md` riêng của module nếu có.
- Không sửa file nào trong bước này.

## 2. Viết plan

Copy `specs/_templates/plan.md` → `specs/<ID>/plan.md`, điền:

- **Module bị ảnh hưởng**: đánh dấu module dùng chung theo `shared_modules`; liệt kê module phụ thuộc cần chạy test. Không được có module trong `third_party_modules`.
- **Thiết kế**: theo quy ước Odoo 18 trong `AGENTS.md` (view `<list>`, `invisible=`, `@api.model_create_multi`, `check_company`, `compare_amounts`, SQL tham số hóa...).
- **Chiến lược test**: mỗi AC trong spec ↔ ít nhất một test (tên test bắt đầu `test_ac<n>_`). Thêm test quyền/multi-company nếu spec có.
- **Phân chia theo mức dùng AI** (lấy `ai_level` từ spec):
  - Cao: AI viết tất cả, TC đọc lại.
  - Trung bình: AI viết test, field, view, security; logic nghiệp vụ đánh dấu TC viết hoặc soát từng dòng.
  - Thấp: AI chỉ viết test và plan; **toàn bộ logic lõi đánh dấu TC**.
- **Rủi ro**: đặc biệt dữ liệu cũ, đồng thời (cần khóa dòng?), hiệu năng record rule, ảnh hưởng chéo.
- Plan **không được** thêm yêu cầu ngoài spec. Thấy spec thiếu → ghi vào mục Rủi ro và đề nghị cập nhật spec.

Đặt `status: Draft`. Thêm dòng vào Lịch sử của spec: `<ngày> | AI | Tạo plan`.

## 3. Báo lại người dùng

- Tóm tắt 5 dòng: module, field mới, số test dự kiến, module dùng chung (có/không), phần TC phải tự viết.
- Rủi ro chính.
- Bước tiếp theo: TC duyệt plan (`status: Approved`, điền `technical_approver`) → `/sdd-tasks <ID>`.
