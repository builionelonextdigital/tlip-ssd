---
name: shared-module-review
description: Checklist review của pod Core cho thay đổi trong module dùng chung tlip_approval, tlip_access_rights, pcv_minvoice, pcv_mysign. Dùng khi review merge request hoặc diff đụng tới các module này, hoặc khi tự kiểm tra trước khi mở merge request.
---

# Review thay đổi ở module dùng chung

Các module này dùng chung cho O2C và P2P. Một thay đổi sai làm hỏng nhiều luồng cùng lúc.

## Phạm vi ảnh hưởng

`approval.matrix.mixin` (tlip_approval) đang được kế thừa bởi:
- tlip_account: `account.move` (RFP, hóa đơn), `account.payment`, `batch.payment`, `budget.allocation.approval`, `account.analytic.account`
- tlip_account_asset: `account.asset`, `asset.modify.cr`
- tlip_procurement: `request.purchase` (F1), `procurement.task` (F2), `task.order.selection`, `purchase.agreement.base` (hợp đồng)
- tlip_approval: `res.partner`, `res.partner.cr`
- tlip_leasing: `leasing.agreement.base`, `stock.location.cr`
- tlip_stock: `stock.location`, `stock.picking`
- tlip_utilities: `electricity.consumption`, `water.consumption`
- tlip_sign_ticket: `sign.ticket`

Kiểm tra lại bằng:

```bash
grep -rn "approval.matrix.mixin" --include=*.py . | grep -v "_name ="
```

## Checklist

1. **Lấy diff**: `git diff <base>...HEAD -- tlip_approval tlip_access_rights pcv_minvoice pcv_mysign`.
2. **Ảnh hưởng chéo**: thay đổi field/hàm của mixin có làm hỏng model kế thừa nào không (override cùng tên, `super()` bị bỏ).
3. **Quyền**:
   - Mọi dòng ACL mới có group; không cấp write/create/unlink cho `base.group_user` trên dữ liệu kế toán.
   - Record rule có điều kiện công ty; rule theo user/job không mở rộng quyền ngoài ý muốn (AUDIT #23).
   - `sudo()` mới có lý do và giới hạn bản ghi.
4. **Trạng thái duyệt**: không cho ghi `approval_state` từ RPC; withdraw/cancel kiểm tra owner và trạng thái (AUDIT #5); chứng từ đã duyệt bị khóa (AUDIT #24).
5. **Tích hợp ngoài** (`pcv_*`): có timeout, có khóa chống gửi 2 lần, không log secret, test dùng mock.
6. **Hiệu năng**: record rule không dùng domain gọi hàm nặng; compute stored có `@api.depends` đủ.
7. **Test**: có test cho thay đổi; chạy test của `tlip_approval`, `tlip_access_rights` và các module phụ thuộc (`tlip_account`, `tlip_procurement`, `tlip_leasing`, `tlip_account_asset`).
8. **Migration**: version manifest tăng; thay đổi rule/ACL được cập nhật khi `-u` (kiểm tra `noupdate`).

## Kết quả review

Trả về bảng: mục checklist | Đạt / Không đạt / Không áp dụng | ghi chú (file:dòng). Kết luận: **Chấp thuận**, **Chấp thuận có điều kiện** (liệt kê) hoặc **Cần sửa**.
