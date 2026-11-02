# specs/

Mỗi hạng mục một thư mục `specs/<PREFIX>-<NUM>/` (VD `specs/O2C-14/`):

| File | Nội dung | Ai duyệt |
|---|---|---|
| `spec.md` | Cần gì: yêu cầu, tiêu chí nghiệm thu (AC), câu hỏi mở | FC + TC |
| `plan.md` | Làm thế nào: module, model/field, bảo mật, test | TC |
| `tasks.md` | Checklist thực thi, test trước | — |

Vòng đời `status` của spec: `Draft → In Review → Approved → Implementing → Done` (hoặc `Dropped`).

- Chỉ người duyệt đổi sang `Approved` và điền `business_approver` / `technical_approver` (tên + ngày).
- CI (`ci/check_specs.py`) chặn commit `[<mã>]` nếu spec chưa ở `Approved`/`Implementing`/`Done`.
- Mẫu: `_templates/`. Ví dụ hoàn chỉnh: repo `ai-kit-odoo-18`, thư mục `examples/sample-spec/`.
