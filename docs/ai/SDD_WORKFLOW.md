# Quy trình Spec-Driven Development (SDD)

Áp dụng cho TC, FC, PM và pod Core. Đi kèm `AGENTS.md` và `sdd.config.yml`.

## Vì sao

- Yêu cầu đang nằm rải rác trong tracker, docx, biên bản họp, chat → AI và người mới đều phải đoán.
- Review code khó khi không có chuẩn để so: "đúng" theo ai?
- Code do AI viết nhanh, nên cái chậm (hiểu sai yêu cầu) càng đắt.

SDD đưa yêu cầu vào repo dưới dạng **spec có tiêu chí nghiệm thu kiểm tra được**, duyệt trước khi code. Test được viết từ chính các tiêu chí đó.

## Vai trò

| Vai trò | Việc |
|---|---|
| **TC** | Chạy `/sdd-spec`, `/sdd-plan`...; duyệt kỹ thuật spec & plan; viết logic lõi khi mức AI thấp; chịu trách nhiệm MR |
| **FC** | Trả lời câu hỏi mở; duyệt nghiệp vụ spec (đặc biệt bảng AC và số liệu) |
| **Pod Core** | Review khi đụng module dùng chung |
| **PM** | Theo dõi trạng thái spec; thu số liệu thí điểm |
| **AI** | Soạn spec/plan/tasks, viết test, viết code trong giới hạn `ai_level`, kiểm tra |

## Luồng

```
1. /sdd-spec <mã>    AI soạn spec + câu hỏi mở             status: Draft
2. FC trả lời câu hỏi, TC/FC sửa trực tiếp file            status: In Review
3. FC + TC duyệt: điền business_approver/technical_approver status: Approved   ← CỔNG 1
4. /sdd-plan <ID>    AI khảo sát code, viết plan
5. TC duyệt plan                                             plan status: Approved ← CỔNG 2
6. /sdd-tasks <ID>   checklist
7. /sdd-implement    test trước → code; dừng ở task TC        status: Implementing
8. /sdd-verify       AC ↔ test, checklist, mô tả MR
9. MR → review → (pod Core) → merge → UAT → TC đổi           status: Done
```

Cách duyệt: commit thay đổi `status` + tên người duyệt vào nhánh của hạng mục, hoặc mở MR riêng chỉ chứa spec (khuyến nghị cho hạng mục lớn: FC comment trực tiếp trên MR GitLab).

## Khi yêu cầu thay đổi giữa chừng

1. Sửa `spec.md` trước, thêm dòng vào mục Lịch sử, đưa `status` về `In Review`.
2. Đổi AC → FC duyệt lại. Chỉ đổi chi tiết kỹ thuật → TC duyệt lại plan.
3. Chạy `/sdd-plan`, `/sdd-tasks` để cập nhật; rồi tiếp tục `/sdd-implement`.

## Ngoại lệ

Tiền tố trong `exempt_prefixes` (VD `HOTFIX`, `AUDIT`, `CHORE`) không bắt buộc spec. Dùng tiết chế; hotfix lớn hơn 1 ngày công vẫn nên có spec.

## Gate CI

`ci/check_specs.py` chạy trên merge request:

- Với mỗi commit có mã hạng mục → phải có `specs/<ID>/spec.md` ở trạng thái cho phép và có tên người duyệt.
- Cảnh báo (không chặn) nếu `tasks.md` còn task chưa xong.

## Đo hiệu quả (thí điểm)

Ghi cho mỗi hạng mục thí điểm:

| Mã | MD ước lượng | MD thực tế | Mức AI | Số vòng sửa spec | Lỗi ở review | Lỗi ở UAT | Ghi chú |
|---|---|---|---|---|---|---|---|

Tiêu chí áp rộng: MD thực tế không vượt ước lượng, lỗi UAT không tăng so với hạng mục làm theo cách cũ, FC/TC đánh giá spec giúp review nhanh hơn.
