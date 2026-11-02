# SDD Studio trên GitHub – Hướng dẫn vận hành

Mỗi hạng mục là **một Issue trên board**. Mọi bước SDD được gọi bằng một comment `@claude ...`. Mỗi cổng duyệt là **một PR merge vào `main`**. Không ai phải nhớ lệnh terminal; TC chỉ cần terminal để chạy test Odoo trên máy local.

## 1. Board

Project "TLIP SDD" có các cột (trường Status), tương ứng nhãn `status:*` trên Issue:

| Cột | Nghĩa | Ai đẩy sang cột tiếp |
|---|---|---|
| Backlog | Có Issue, chưa có spec | TC: comment `@claude /sdd-spec` |
| Spec Draft | Claude đã mở PR spec | Claude / TC |
| Spec Review | Chờ FC + TC duyệt spec | FC + TC duyệt PR spec |
| Spec Approved | PR spec đã merge | TC: `@claude /sdd-plan` |
| Plan Review | Chờ TC duyệt plan | TC duyệt PR plan |
| Ready to build | Spec + plan đã merge | TC: `@claude /sdd-tasks` rồi `/sdd-implement` |
| Implementing | Đang có PR code | Reviewer + pod Core |
| Done | Đã merge, qua UAT | TC đổi spec `status: Done` |
| Dropped | Hủy | PM |

Nhãn và cột do workflow **SDD board sync** tự cập nhật theo `status` trong `spec.md` / `plan.md`. Không kéo thẻ bằng tay. Muốn đổi cột thì sửa file spec.

Lọc nhanh trên board: `label:ai:thap`, `label:shared-module`, `label:pod:o2c`.

## 2. Một hạng mục từ đầu đến cuối

| # | Ai | Làm ở đâu | Thao tác |
|---|---|---|---|
| 1 | PM/TC | Issues → New → "Hạng mục SDD" | Điền form. Hoặc tạo hàng loạt từ tracker (mục 4) |
| 2 | TC | Comment trong Issue | `@claude /sdd-spec` |
| 3 | Claude | — | Soạn `specs/<ID>/spec.md` từ nội dung Issue, mở PR "Spec", trả lời bằng danh sách câu hỏi mở |
| 4 | FC | PR Spec → tab *Files changed* | Đọc AC, trả lời câu hỏi mở (comment trên dòng, hoặc nút *Edit file*) |
| 5 | TC | PR Spec | Muốn Claude sửa thì comment `@claude cập nhật spec theo trả lời của FC ở trên` |
| 6 | FC + TC | PR Spec → *Edit file* | Điền `business_approver`, `technical_approver` (tên + ngày), đổi `status: Approved`. TC approve và **merge** PR → **Cổng 1** |
| 7 | TC | Comment trong Issue | `@claude /sdd-plan` → Claude mở PR "Plan" |
| 8 | TC | PR Plan | Đọc plan, đổi plan `status: Approved` + `technical_approver`, **merge** → **Cổng 2** |
| 9 | TC | Comment trong Issue | `@claude /sdd-tasks và /sdd-implement` → Claude mở PR code (Draft) |
| 10 | TC | Máy local | `gh pr checkout <số PR>`, chạy test Odoo (`test_command` trong `sdd.config.yml`), sửa nếu cần, tick task trong `tasks.md`, push |
| 11 | TC | PR code | `@claude /sdd-verify` → Claude đối chiếu AC ↔ test và cập nhật mô tả PR |
| 12 | Reviewer (+ pod Core) | PR code | Review theo spec và plan; check "SDD check" phải xanh; merge |
| 13 | TC | Sau UAT | Sửa spec `status: Done` (commit nhỏ vào `main` qua PR) → thẻ sang Done |

Hạng mục **mức AI Thấp**: ở bước 9 chỉ gọi `@claude /sdd-tasks và viết test`. Logic lõi do TC tự viết ở bước 10.

## 3. Câu lệnh hay dùng trong comment

| Comment | Kết quả |
|---|---|
| `@claude /sdd-spec` | Soạn spec từ Issue, mở PR spec |
| `@claude /sdd-plan` | Khảo sát code, viết plan, mở PR plan (dừng nếu spec chưa duyệt) |
| `@claude /sdd-tasks và /sdd-implement` | Tách task, viết test + code theo mức AI, mở PR code |
| `@claude /sdd-verify` (trong PR) | Bảng AC → test, checklist, mô tả PR |
| `@claude giải thích hàm <tên>` | Giải thích code cũ, không sửa gì |
| `@claude sửa theo review ở trên` (trong PR) | Sửa và push lên chính nhánh PR |

Chỉ người có quyền **write** trên repo mới kích hoạt được `@claude`. Mỗi lần chạy tốn phút GitHub Actions và token Claude: viết yêu cầu cụ thể, mỗi comment một việc.

## 4. Tạo Issue hàng loạt từ tracker

Chạy trên máy TC, vì tracker chỉ có bản local:

```bash
python3 tools/tracker_to_issues.py --only O2C --show-body     # xem trước, không tạo gì
python3 tools/tracker_to_issues.py --only O2C --apply         # tạo Issue (bỏ qua mã đã có)
```

Script chỉ chép các cột thiết kế giải pháp. **Đọc bản xem trước**: không được có tên khách thật, số tiền thật hay dữ liệu đo thật. Mã có 2 dòng trong tracker (O2C No. 13, 16) được gộp vào một Issue và đánh dấu để FC chốt.

## 5. Giới hạn cần biết

- Runner GitHub **không có Odoo** (image Enterprise là private), nên Claude viết test nhưng không chạy được. Test luôn do TC chạy local trước khi review.
- Claude trên GitHub **không thấy** `Project-infomations/`. Thông tin chỉ có trong docx hoặc biên bản họp thì FC/TC dán đoạn liên quan vào Issue.
- Claude không bao giờ tự duyệt, không đổi `Approved` / `Done`, không push vào `main`.
- Code Claude viết vẫn qua đủ các cổng trong `docs/ai/AI_USAGE.md`: test, review chéo, pod Core, UAT.

## 6. Cài đặt (một lần)

1. Merge PR thêm SDD Studio.
2. `./tools/setup_github.sh`: tạo nhãn và in các bước làm tay.
3. Cài Claude GitHub App, thêm secret `ANTHROPIC_API_KEY`.
4. Tạo Project board, trường Status đúng 9 lựa chọn ở mục 1. Tùy chọn: thêm `PROJECT_TOKEN`, `PROJECT_OWNER`, `PROJECT_NUMBER` để board tự chuyển cột.
5. Branch protection cho `main`.
6. Thử với một hạng mục nhỏ (O2C No. 14).
