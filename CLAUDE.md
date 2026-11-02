# CLAUDE.md

@AGENTS.md

## Riêng cho Claude Code

- Skill có sẵn trong `.claude/skills/`:
  - `sdd-spec` → `sdd-plan` → `sdd-tasks` → `sdd-implement` → `sdd-verify`: quy trình SDD cho mọi hạng mục O2C/P2P (xem `AGENTS.md` mục 8).
  - `odoo-feature`: lối tắt chạy lần lượt các bước SDD cho một hạng mục trong tracker (O2C/P2P/Kế toán) từ đầu đến merge request.
  - `odoo-test`: viết và chạy test cho module `tlip_*`.
  - `fix-audit-finding`: sửa một lỗi trong báo cáo audit (`AUDIT #x`).
  - `shared-module-review`: checklist review khi đụng `tlip_approval`, `tlip_access_rights`, `pcv_minvoice`, `pcv_mysign`.
- Một số module có `CLAUDE.md` riêng với lưu ý chi tiết; đọc khi làm việc trong module đó.
- Hạng mục **Mức dùng AI = Thấp**: dùng plan mode, chỉ đưa kế hoạch và test, không tự viết logic lõi.
- `.claude/settings.json` đã chặn đọc file bí mật/dữ liệu thật và chặn push/deploy. Không tìm cách vượt qua.
- Chạy trên GitHub (`@claude` trong Issue/PR): xem `docs/ai/SDD_STUDIO.md`; Project-infomations/ không có trên runner, nguồn yêu cầu là Issue.
