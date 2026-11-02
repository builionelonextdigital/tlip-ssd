---
name: sdd-implement
description: Bước 4 của quy trình SDD – thực thi specs/<ID>/tasks.md theo đúng spec và plan đã duyệt trên repo Odoo 18, test trước rồi code, tôn trọng mức dùng AI (Thấp = không viết logic lõi), cập nhật trạng thái từng task. Dùng khi người dùng nói "/sdd-implement <ID>", "làm tiếp task", hoặc "code hạng mục <mã>" khi đã có tasks.md.
---

# /sdd-implement – Thực thi task

## 0. Cổng kiểm tra

1. Đọc `AGENTS.md`, `sdd.config.yml`, `specs/<ID>/spec.md`, `plan.md`, `tasks.md`.
2. Spec `Approved`/`Implementing` và plan `Approved`. Không đạt → dừng.
3. Spec đang `Approved` → đổi sang `Implementing`, ghi Lịch sử.
4. Đọc `ai_level` trong spec. Đây là giới hạn cứng:

| ai_level | AI được làm | AI dừng ở |
|---|---|---|
| Cao | Mọi task `AI` | — |
| Trung bình | Task `AI`; task `TC` chỉ khi người dùng yêu cầu rõ trong phiên này | Task `TC` |
| Thấp | Task test, field, view, security, i18n, version | Mọi task logic (`TC`) – chỉ được giải thích, gợi ý cấu trúc hàm, không viết thân hàm |

## 1. Vòng lặp mỗi task

1. Chọn task `[ ]` đầu tiên theo thứ tự mà AI được làm. Đánh `[~]`.
2. Làm đúng phạm vi task. Giữ diff nhỏ; không refactor phần không liên quan; không sửa module trong `third_party_modules`.
3. Task test: chạy và xác nhận **FAIL đúng lý do** trước khi viết chức năng.
4. Task code: chạy lại test liên quan (lệnh `test_command` trong config, thay `{module}`, `{tags}`).
5. Đánh `[x]`, thêm ghi chú ngắn nếu có quyết định đáng chú ý. Không đạt → để `[~]`, ghi lỗi.
6. Đến task `TC` (hoặc bị chặn bởi ai_level): dừng vòng lặp, báo người dùng.

## 2. Khi phát hiện spec/plan sai hoặc thiếu

**Dừng.** Không tự "sửa cho đúng" trong code. Báo người dùng: chỗ nào, đề xuất sửa spec/plan. Chỉ tiếp tục khi spec/plan được cập nhật (và duyệt lại nếu thay đổi yêu cầu hoặc AC).

## 3. Không được

- Không commit, push, deploy (để TC làm). Nếu người dùng yêu cầu commit: message bắt đầu bằng `[<Mã gốc>]`.
- Không sửa `status` của plan; không đánh `Done` cho spec.
- Không làm test "qua cho có": không xóa assert, không skip test, không sửa AC trong test cho khớp code.

## 4. Báo lại người dùng (tiếng Việt)

- Task đã xong / còn lại / chờ TC.
- File đã sửa.
- Test đã chạy: số test, số qua, lỗi đầu tiên.
- Điểm cần TC/FC xác nhận.
