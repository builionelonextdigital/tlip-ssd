# SDD Studio – Claude Code web + GitHub

Toàn bộ quy trình SDD chạy trên hai nơi, không cần VS Code hay terminal:

- **GitHub**: board "TLIP SDD", Issue, Pull Request, review, duyệt.
- **Claude Code web** (claude.ai/code, hoặc tab **Code** trong app Claude với môi trường **Cloud**): Claude soạn spec, plan, code, rồi push lên nhánh và mở PR.

Mỗi người dùng **gói Claude của mình**. Repo không cần `ANTHROPIC_API_KEY`.

## 1. Thiết lập

### Mỗi người (một lần)

1. Vào **claude.ai/code** → kết nối GitHub (Claude GitHub App) → chọn repo `builionelonextdigital/tlip-ssd`.
2. Môi trường: giữ **Default** (Trusted network).
3. Kiểm tra: mở session mới, gõ `/` — phải thấy `sdd-spec`, `sdd-plan`, `sdd-tasks`, `sdd-implement`, `sdd-verify`.

Tài khoản dùng cho code TLIP phải theo `docs/ai/AI_USAGE.md`. Nên dùng gói **Team/Enterprise** của công ty. Tài khoản Pro/Max cá nhân chỉ dùng khi PM đã xác nhận.

### Repo (đã làm, ghi lại để tham khảo)

| Thành phần | Vai trò |
|---|---|
| Board "TLIP SDD" (`github.com/users/builionelonextdigital/projects/1`) | Mỗi hạng mục một thẻ, cột = trạng thái spec |
| Issue Form "Hạng mục SDD", `tools/tracker_to_issues.py` | Tạo hạng mục |
| Workflow **SDD board sync** | Đổi nhãn `status:*` và cột trên board theo `spec.md` / `plan.md` |
| Workflow **SDD check** | PR có commit code phải có spec + plan đã `Approved` |
| Workflow **Claude (SDD)** | **Tắt** (Actions → Claude (SDD) → ⋯ → Disable workflow). Chỉ bật lại khi công ty có API key chung |

## 2. Board

| Cột | Nghĩa | Ai đẩy sang cột tiếp |
|---|---|---|
| Backlog | Có Issue, chưa có spec | TC chạy `/sdd-spec` trên Claude Code web |
| Spec Draft | PR spec đã mở | FC + TC đọc |
| Spec Review | Spec chờ duyệt (`status: In Review`) | FC + TC duyệt |
| Spec Approved | Spec `Approved`, chưa có plan | TC chạy `/sdd-plan` |
| Plan Review | Plan chờ TC duyệt | TC duyệt |
| Ready to build | Spec + plan đã duyệt | TC chạy `/sdd-tasks`, `/sdd-implement` |
| Implementing | Đang code (`status: Implementing`) | Reviewer + pod Core |
| Done | Đã merge, qua UAT (`status: Done`) | — |
| Dropped | Hủy | PM |

Thẻ **tự chuyển cột** mỗi khi PR có thay đổi trong `specs/`. Không kéo thẻ bằng tay; muốn đổi cột thì đổi `status` trong file spec/plan.

## 3. Một hạng mục từ đầu đến cuối

Quy ước: **một hạng mục = một session Claude = một nhánh = một PR**. Spec, plan và code đều nằm trong cùng PR; PR chỉ được merge ở cuối.

| # | Ai | Ở đâu | Thao tác |
|---|---|---|---|
| 1 | PM/TC | GitHub → Issues → New → "Hạng mục SDD" | Tạo Issue (hoặc PM tạo hàng loạt từ tracker, mục 6). Copy link Issue |
| 2 | TC | claude.ai/code → **New session**, repo `tlip-ssd`, nhánh `main` | Gõ: `/sdd-spec O2C No. 14 – nguồn: <link Issue>`. Đổi tên session thành `O2C-14` |
| 3 | TC | Claude Code web | Đọc spec trong khung **Changes**, comment trên dòng cần sửa, gửi cho Claude. Xong thì nhờ: `push và mở PR draft, tiêu đề "[O2C No. 14] <tên>", body "Refs #<số Issue>"` |
| 4 | FC | GitHub → PR → **Files changed** | Đọc bảng tiêu chí nghiệm thu (AC), trả lời câu hỏi mở bằng comment trên dòng |
| 5 | TC | Claude Code web (cùng session) | `cập nhật spec theo các comment của FC trên PR` → Claude sửa và push |
| 6 | FC + TC | GitHub → PR → `specs/O2C-14/spec.md` → **⋯ → Edit file** | Điền `business_approver`, `technical_approver` (tên + ngày), đổi `status: Approved`, **Commit changes** vào nhánh PR → **Cổng 1** |
| 7 | TC | Claude Code web | `/sdd-plan O2C-14` → Claude push `plan.md` lên cùng PR |
| 8 | TC | GitHub → PR → **Edit file** `plan.md` | Đọc plan, đổi `status: Approved` + `technical_approver` → **Cổng 2** |
| 9 | TC | Claude Code web | `/sdd-tasks O2C-14`, rồi `/sdd-implement O2C-14` |
| 10 | TC | Claude Code web | Đọc từng file trong **Changes**; comment để Claude sửa. Mức AI **Thấp**: TC tự viết logic lõi bằng **Edit file** trên GitHub, rồi nhờ Claude review |
| 11 | TC | Claude Code web | `/sdd-verify O2C-14` → `cập nhật mô tả PR theo kết quả verify` |
| 12 | TC | Claude Code web → menu **⋮** cạnh PR trong khung Changes | Bật **Auto-fix**: Claude tự sửa khi CI đỏ hoặc có comment review |
| 13 | TC | GitHub → PR | **Ready for review**, gắn reviewer (+ pod Core nếu nhãn `shared-module`) |
| 14 | Reviewer | GitHub → PR | Review theo spec + plan; check **SDD check** xanh; **Merge** |
| 15 | TC | GitHub | Sau UAT: **Edit file** `spec.md` trên `main` (qua PR nhỏ), `status: Done` → thẻ sang Done |

Session nằm trong danh sách bên trái của claude.ai/code; mở lại từ máy tính hoặc điện thoại để làm tiếp. Session để lâu không dùng sẽ khởi động lại môi trường nhưng giữ nguyên lịch sử chat.

## 4. Câu lệnh mẫu trong Claude Code web

| Gõ | Kết quả |
|---|---|
| `/sdd-spec O2C No. 14 – nguồn: <link Issue>` | Soạn spec từ Issue, liệt kê câu hỏi mở |
| `push và mở PR draft "[O2C No. 14] <tên>", body "Refs #4"` | Tạo nhánh + PR |
| `cập nhật spec theo comment của FC trên PR #<số>` | Sửa spec, push |
| `/sdd-plan O2C-14` | Plan; tự dừng nếu spec chưa `Approved` |
| `/sdd-tasks O2C-14` rồi `/sdd-implement O2C-14` | Test + code theo mức dùng AI |
| `/sdd-verify O2C-14` | Bảng AC → test, checklist, mô tả PR |
| `giải thích hàm <tên> trong <file>` | Đọc code cũ, không sửa |
| `rebase nhánh lên main` | Khi PR bị xung đột |

Mỗi tin nhắn một việc, nói rõ mã hạng mục. Claude không được tự đổi `Approved` / `Done` hay điền người duyệt: việc đó luôn làm bằng **Edit file** trên GitHub.

## 5. Giới hạn và cách xử lý

| Giới hạn | Cách xử lý |
|---|---|
| Claude Code web **không thấy `Project-infomations/`** (không có trong git) | Nguồn của `/sdd-spec` là Issue. Đoạn nào chỉ có trong docx / biên bản họp: dán vào Issue hoặc vào chat. Không dán dữ liệu thật của khách |
| **Không chạy được test Odoo** trên môi trường cloud (không có image Odoo Enterprise) | Claude viết test và ghi rõ "chưa chạy". Test do người có môi trường Odoo chạy trước khi merge, hoặc dùng workflow "Odoo tests" trên GitHub khi đã có (cần deploy token registry GitLab) |
| Session dùng hạn mức gói Claude của từng người | Viết yêu cầu cụ thể; dùng `/compact` khi session dài |
| Đọc Issue từ link không được | Copy nội dung Issue dán vào tin nhắn đầu |

## 6. Tạo Issue hàng loạt từ tracker (PM, khi cần)

Việc này cần tracker bản local nên PM làm một lần cho mỗi đợt, trên máy có repo và `Project-infomations/`:

```bash
python3 tools/tracker_to_issues.py --only O2C --show-body   # xem trước
python3 tools/tracker_to_issues.py --only O2C --apply       # tạo, bỏ qua mã đã có
```

Đọc bản xem trước, đảm bảo không có dữ liệu thật của khách hàng. Không làm được bước này thì tạo Issue bằng form trên GitHub và dán nội dung từ tracker.

## 7. Quy tắc giữ nguyên

- Không code khi spec hoặc plan chưa `Approved` (AGENTS.md mục 8).
- Mức dùng AI **Thấp**: AI không viết logic lõi.
- Module dùng chung: pod Core review bắt buộc.
- Code AI viết đi qua đủ các cổng trong `docs/ai/AI_USAGE.md`: test, review chéo, pod Core, UAT.
