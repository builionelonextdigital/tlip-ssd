# tlip_access_rights – lưu ý cho AI

**Module dùng chung.** Mọi thay đổi cần pod Core review (skill `shared-module-review`).

- Chứa nhóm quyền và record rule cho mọi phân hệ: `security/account_move_security.xml`, `account_payment_security.xml`, `budget_security.xml`, `procurement_security.xml`, `leasing_security.xml`, `utility_security.xml`, `development_security.xml`, `security.xml`.
- Dữ liệu 3 pháp nhân dùng chung database: mọi rule phải có điều kiện `company_id in company_ids`.
- Lỗi đã biết: AUDIT #18 (mọi user nội bộ full CRUD bút toán và payment, nằm ở `tlip_account`), #23 (rule theo job). Mức Medium: nhiều ACL full CRUD cho mọi user nội bộ.
- Hạng mục O2C No. 23 cần ma trận phân quyền từ TLIP (đang chờ xác nhận). Không tự đặt ra ma trận; hỏi FC.
- Mỗi rule mới cần test với `with_user()` cho cả trường hợp được phép và bị chặn.
- Rule trong file có `noupdate="1"` sẽ không cập nhật khi `-u`; cần migration hoặc bỏ noupdate có chủ đích.
