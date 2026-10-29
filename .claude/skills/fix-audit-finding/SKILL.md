---
name: fix-audit-finding
description: Sửa một lỗi trong báo cáo audit codebase TLIP (TLIP Audit.pdf, 12/10/2026) theo mã AUDIT #1–#25 – tái hiện bằng test, áp dụng cách sửa nhỏ nhất, kiểm tra hồi quy. Dùng khi được giao "sửa AUDIT #x" hoặc lỗi bảo mật/toàn vẹn dữ liệu đã có trong báo cáo.
---

# Sửa lỗi trong báo cáo audit

Báo cáo gốc: `Project-infomations/TLIP Audit.pdf` (review tĩnh, chưa chạy code). Số dòng có thể đã lệch; luôn tìm lại bằng tên hàm.

## Quy trình

1. Đọc dòng `AUDIT #x` trong bảng dưới. Mở file, tìm đúng hàm.
2. Xác nhận lỗi còn tồn tại (code có thể đã được sửa). Nếu đã sửa, báo người dùng và dừng.
3. Viết test tái hiện lỗi (skill `odoo-test`), chạy và thấy **fail**.
4. Áp dụng cách sửa nhỏ nhất. Không refactor rộng.
5. Chạy lại test của module và module phụ thuộc. Lỗi ở `tlip_approval`, `tlip_access_rights`, `pcv_*` cần pod Core review.
6. Commit message: `[AUDIT #x] <mô tả ngắn>`.

## 25 lỗi mức cao

| # | Nhóm | Lỗi | Vị trí | Cách sửa nhỏ nhất |
|---|---|---|---|---|
| 1 | Security | Mật khẩu M-invoice, secret/token MySign mọi user đọc được; user thường sửa được `minvoice.account` | `pcv_minvoice/models/minvoice_account.py`, `pcv_mysign/models/mysign_config.py`, `mysign_account.py`, 2 file ACL | `groups="base.group_system"` trên field; bỏ quyền write/create của `base.group_user` |
| 2 | Integrity | Hóa đơn điện tử có thể phát hành 2 lần (transaction id bị rollback, không khóa dòng) | `pcv_minvoice/wizards/minvoice_action_wizard.py` | Lưu id trước khi POST, khóa move `FOR UPDATE NOWAIT` |
| 3 | Integrity | Ký MySign không khóa, không idempotent | `pcv_mysign/controllers/mysign.py` | Khóa dòng signer, đặt trạng thái đang ký trước khi gọi ngoài |
| 4 | Reliability | Gọi HTTP ra ngoài không có timeout | `pcv_minvoice/utils/minvoice_api_helper.py`, `pcv_mysign/utils/mysign_api_helper.py` | `timeout=(5, 30)` |
| 5 | Security | Ai cũng withdraw/cancel được approval request, kể cả đã duyệt (chạy `sudo()`) | `tlip_approval/wizard/withdraw_approval_wizard.py`, `models/approval_request.py` | Chỉ owner và khi đang pending |
| 6 | Business | Duyệt nhiều cấp không được áp dụng (`approval_minimum` không dùng) | `tlip_approval/models/approval_category.py`, `wizard/submit_approval_wizard.py` | Truyền minimum vào request hoặc đánh dấu mọi approver required |
| 7 | Security | Trạng thái procurement/approval ai cũng ghi được; `action_reset` không chặn | `tlip_procurement/models/request_purchase.py`, `task_order_selection.py` | Chặn ghi state, kiểm tra lại maximum trong `action_confirm` |
| 8 | Integrity | Cron hằng ngày tạo trùng hợp đồng thuê theo phụ lục | `tlip_leasing/models/leasing_supplement.py` | Chuyển phụ lục sang trạng thái kết thúc sau khi có hiệu lực |
| 9 | Reliability | Cron FX-out tháng luôn lỗi (thiếu tham số month, year) | `tlip_fx_out/data/fx_out_cron_monthly.xml` | Tính tháng trước ngay trong cron |
| 10 | Security | ACL tỷ giá FX-out không có group (mọi user, cả portal) | `tlip_fx_out/security/ir.model.access.csv` | Gán nhóm kế toán trưởng |
| 11 | Reliability | Ngày đồng bộ điện nước bị đóng băng lúc khởi động server | `tlip_utilities/models/electricity_point.py`, `water_point.py` | Default `None`, tính trong hàm |
| 12 | Accounting | Báo cáo đối chiếu ngân hàng cộng cả dòng nháp/hủy, không lọc công ty | `tlip_account/reports/bank_reconciliation_report.py` | Lọc dòng posted và công ty, sửa tổng bank |
| 13 | Accounting | Hạn thanh toán theo ngày làm việc không được áp dụng | `tlip_account/models/account_move.py` (write) | Điều chỉnh vals trước `super()`, dùng `any()` |
| 14 | E-invoice | Credit note và dòng âm gửi thành số dương | `pcv_minvoice/wizards/minvoice_action_wizard.py` | Đổi dấu theo `price_subtotal` và `move_type` |
| 15 | E-invoice | Mã thuế `str(int(rate))`: không thuế, KCT, 0% đều gửi "0"; chỉ đọc thuế đầu tiên | `minvoice_action_wizard.py` | Map từng thuế sang mã M-invoice; từ chối dòng 0 hoặc 2+ thuế |
| 16 | E-invoice | Tổng header làm tròn khác các dòng, lệch vài đồng | `pcv_minvoice/utils/minvoice_helper.py` | Tính header từ các dòng đã làm tròn |
| 17 | E-invoice | Hóa đơn đã phát hành vẫn reset draft, sửa, xóa được | `tlip_account/models/account_move.py` (`button_draft`) | Chặn `button_draft`, `unlink`, ghi số tiền khi đã phát hành |
| 18 | Security | Mọi user nội bộ full CRUD `account.move`, `account.move.line`, `account.payment` | `tlip_account/security/ir.model.access.csv`, `security/account_security.xml` | Bỏ 3 dòng ACL |
| 19 | Security | Context `force_post`, `bypass_period_closing`, `skip_accounting_period_check` nhận từ mọi RPC | `tlip_account/models/account_move.py`, `accounting_period_closing.py` | Chỉ chấp nhận trong `sudo()` hoặc với kế toán trưởng |
| 20 | Accounting | Kiểm tra kỳ chỉ một phía, post được vào kỳ tương lai | `accounting_period_closing.py` | Từ chối cả ngày sau cuối kỳ |
| 21 | Budget | Điều chuyển ngân sách chỉ kiểm tra lúc submit; duyệt đồng thời làm âm nguồn | `tlip_account/models/budget_allocation_approval.py` | Kiểm tra lại với row lock khi approve |
| 22 | Budget | Nguồn trừ theo tháng phát hành (UTC), đích cộng theo tháng dòng | `tlip_account/models/budget_line.py` | Trừ theo từng dòng phân bổ và tháng |
| 23 | Security | User không có job position thấy và sửa mọi request duyệt theo user | `tlip_approval/security/approval_security.xml` | Thêm `('job_id','!=',False)` vào rule |
| 24 | Business | Sau submit vẫn sửa được số tiền, đối tác, dòng khi pending/approved | `tlip_approval/models/approval_matrix_mixin.py`, `approval_request.py` | Chặn sửa field đã lọc khi pending/approved |
| 25 | Integrity | Xóa chứng từ để lại approval request treo (MissingError) | `approval_request.py` | Hủy request liên kết trong `unlink` của mixin |

Liên quan tới hạng mục: O2C No. 23 (phân quyền, khóa chứng từ) bao gồm #5, #17, #18, #24; nên làm cùng nhau.
