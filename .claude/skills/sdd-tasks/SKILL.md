---
name: sdd-tasks
description: Bước 3 của quy trình SDD – tách specs/<ID>/plan.md đã Approved thành checklist specs/<ID>/tasks.md theo thứ tự test trước, mỗi task nhỏ, ghi rõ file và ai làm (AI/TC). Dùng khi người dùng nói "/sdd-tasks <ID>" hoặc "chia task" cho hạng mục đã có plan.
---

# /sdd-tasks – Tách task

## 0. Cổng kiểm tra

- `specs/<ID>/spec.md` có `status: Approved` (hoặc `Implementing`).
- `specs/<ID>/plan.md` có `status: Approved` và `technical_approver`. Không có → dừng, báo người dùng.

## 1. Tạo tasks.md

Copy `specs/_templates/tasks.md` → `specs/<ID>/tasks.md` rồi thay phần ví dụ bằng task thật:

- Thứ tự cố định: **Test → Model/field → Logic → View → Bảo mật → Data/i18n/version/migration → Kiểm tra**.
- Mỗi AC trong spec có một task test riêng (`T? · AI · Test AC<n> → test_ac<n>_...`).
- Mỗi task: một việc, một hoặc vài file, kiểm tra được trong < 1 giờ. Ghi đường dẫn file.
- Cột **Ai** theo mục 6 của plan. Mức dùng AI = Thấp → mọi task logic là `TC`.
- Nếu đụng module dùng chung: thêm task chạy test module phụ thuộc và task `shared-module-review` (nếu dự án có skill này).
- Không thêm task nằm ngoài plan.

## 2. Báo lại người dùng

Số task, số task `TC`, thứ tự đề xuất. Bước tiếp theo: `/sdd-implement <ID>`.
