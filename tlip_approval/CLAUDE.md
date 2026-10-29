# tlip_approval – lưu ý cho AI

**Module dùng chung.** Mọi thay đổi cần pod Core review (skill `shared-module-review`).

- `approval.matrix.mixin` được ~20 model kế thừa (RFP, Payment, F1, F2, hợp đồng, TSCĐ, kho, điện nước...). Sửa mixin là sửa tất cả.
- Người duyệt khai báo theo `user_id`/`job_id` và `sequence` trong `approval.category` + `approval.category.approver`; điều kiện chọn option nằm ở `approval_matrix_mixin.py`.
- Lỗi trong báo cáo audit (tại 28/10/2026 một số lỗi đang được sửa dở trong working copy, chưa commit – chạy `git diff tlip_approval` để biết trạng thái trước khi sửa tiếp): #5 withdraw/cancel không kiểm tra owner; #6 `approval_minimum` không dùng; #23 rule so `job_id` với False; #24 sửa được chứng từ khi đang chờ duyệt/đã duyệt; #25 xóa chứng từ để lại request treo. Mức Medium: tự duyệt chứng từ của mình, chọn option không theo thứ tự, approver theo job không có user thì treo mãi.
- Hạng mục liên quan: O2C No. 23 (khóa chứng từ sau duyệt), P2P No. 15–17, 35, 36.
- P2P No. 35 (thay luồng duyệt bằng module Quy trình của A1) **chưa chốt hướng**. Không refactor lớn module này trước khi TLIP chọn Hướng 1 hay Hướng 2.
- Test luồng duyệt phải chạy với ít nhất 2 user: owner và approver, cộng 1 user không liên quan để kiểm tra bị chặn.
