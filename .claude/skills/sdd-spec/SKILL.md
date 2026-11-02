---
name: sdd-spec
description: Bước 1 của quy trình SDD – tạo hoặc cập nhật specs/<ID>/spec.md cho một hạng mục Odoo (mã kiểu "O2C No. 14", "P2P No. 3") từ tracker và tài liệu giải pháp, gồm yêu cầu, tiêu chí nghiệm thu có số liệu và câu hỏi mở. Dùng khi người dùng nói "viết spec", "/sdd-spec <mã>", hoặc khi bắt đầu một hạng mục mà chưa có spec.
---

# /sdd-spec – Soạn spec cho một hạng mục

Mục tiêu: một file spec mà FC đọc hiểu được nghiệp vụ và TC đọc thấy đủ để lập plan. **Spec mô tả CẦN GÌ, không mô tả code.**

## 0. Chuẩn bị

1. Đọc `sdd.config.yml` ở gốc repo. Thiếu file → báo người dùng chạy `install.sh` hoặc tạo từ `examples/`.
2. Lấy mã hạng mục từ người dùng (VD `O2C No. 14`). Chuẩn hóa ID thư mục: `<PREFIX>-<NUM>` → `specs/O2C-14/`.
3. Đã có `specs/<ID>/spec.md`?
   - Có và `status` là `Approved`/`Implementing`/`Done`: **không sửa trực tiếp**. Hỏi người dùng có muốn mở thay đổi yêu cầu không; nếu có, đổi `status: In Review`, ghi lý do vào mục Lịch sử.
   - Có và là `Draft`/`In Review`: cập nhật theo yêu cầu.
   - Chưa có: copy `specs/_templates/spec.md`.

## 1. Thu thập yêu cầu

- Tracker (`tracker_path`, `tracker_sheet`, cột `tracker_id_column`) – đọc dòng của hạng mục, ví dụ:
  ```bash
  python3 - <<'PY'
  import openpyxl
  path, sheet, col, code = "<tracker_path>", "<tracker_sheet>", "<tracker_id_column>", "<Mã>"
  ws = openpyxl.load_workbook(path, data_only=True, read_only=True)[sheet]
  rows = list(ws.iter_rows(values_only=True))
  hi = next(i for i, r in enumerate(rows) if r and col in r)   # dòng tiêu đề
  head = rows[hi]
  for r in rows[hi + 1:]:
      if r and r[head.index(col)] == code:
          for h, v in zip(head, r):
              if v: print(f"## {h}\n{v}\n")
  PY
  ```
- Tài liệu trong `requirement_docs` (docx/pdf): trích đúng đoạn liên quan; nếu không đọc được, nhờ người dùng dán.
- Biên bản họp liên quan nếu người dùng chỉ ra.
- **Không** đọc dữ liệu thật, file bí mật (theo `AGENTS.md`). Ví dụ số liệu luôn dùng dữ liệu giả.

## 2. Khảo sát nhanh code (chỉ để viết đúng mục 7 của spec)

Grep model/field được nhắc tới để biết field nào **đã có**, field nào **mới**. Không thiết kế giải pháp ở bước này.

## 3. Viết spec

Điền đủ các mục của template:

- **Tiêu chí nghiệm thu (AC)**: dạng Given/When/Then, có số tiền/ngày/công ty cụ thể. Mỗi yêu cầu R có ít nhất một AC. Thêm AC cho các trường hợp biên liên quan: multi-company, quyền, chứng từ đã duyệt/đã post, làm tròn.
- **ai_level**: lấy từ tracker. Không có → để trống và đưa vào câu hỏi mở. Không tự đoán.
- **shared_modules**: `Có` nếu mục 7 chạm module trong `shared_modules` của config.
- **Câu hỏi mở**: mọi chỗ mơ hồ, mâu thuẫn giữa nguồn, hoặc tracker ghi "chưa chốt". Không tự chọn đáp án thay FC.
- Mục Lịch sử: thêm dòng `<ngày> | AI | Tạo/cập nhật bản nháp`.

Đặt `status: Draft`, hoặc `In Review` nếu người dùng nói đã sẵn sàng gửi duyệt.

## 4. Không được

- Không điền `business_approver`, `technical_approver`; không đặt `status: Approved`. Chỉ người duyệt làm việc này.
- Không viết code, không tạo plan trong bước này.
- Không sửa thư mục tài liệu gốc (chỉ đọc).

## 5. Báo lại người dùng

- Đường dẫn file spec.
- Số yêu cầu, số AC.
- **Danh sách câu hỏi mở** cần FC/TC trả lời (nguyên văn).
- Bước tiếp theo: FC + TC duyệt → đổi `status: Approved`, điền tên người duyệt → chạy `/sdd-plan <ID>`.
