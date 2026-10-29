---
name: odoo-test
description: Viết và chạy test tự động cho module tlip_* trên Odoo 18 (TransactionCase, test phân quyền, multi-company, mock API ngoài). Dùng khi cần viết test cho một hạng mục, tái hiện lỗi, hoặc chạy test của module.
---

# Viết test cho module TLIP

Repo hiện **chưa có test** cho các module `tlip_*`. Tạo cấu trúc mới khi chưa có:

```
<module>/tests/__init__.py          # from . import test_<tên>
<module>/tests/test_<tên>.py
```

`<module>/__init__.py` **không** import thư mục `tests` (Odoo tự tìm).

## Mẫu test

```python
from odoo.tests import TransactionCase, Form, tagged
from odoo.exceptions import AccessError, UserError, ValidationError


@tagged("post_install", "-at_install")
class TestRfpPayment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer Alpha"})
        # Tạo dữ liệu tối thiểu ngay trong test, không dựa vào dữ liệu có sẵn trên database
        cls.user_accountant = cls.env["res.users"].create({
            "name": "Test Accountant",
            "login": "test_accountant",
            "groups_id": [(6, 0, [cls.env.ref("account.group_account_user").id])],
        })

    def test_unposted_rfp_can_be_matched(self):
        # Arrange - Act - Assert, mỗi test kiểm tra một tiêu chí nghiệm thu
        ...
```

Lưu ý: Odoo 18 dùng `groups_id` trên `res.users` (`group_ids` là tên của bản 19, không dùng).

## Những loại test cần có

| Loại | Khi nào | Cách viết |
|---|---|---|
| Nghiệp vụ | Mọi hạng mục | Dùng ví dụ số liệu trong tài liệu giải pháp (VD: O2C No. 9 khoản 300.000.000 đ phân bổ FIFO cho 4 RFP) |
| Phân quyền | Thay đổi ACL, record rule, khóa chứng từ | `record.with_user(user).write(...)` trong `with self.assertRaises(AccessError)` |
| Multi-company | Model có `company_id`, báo cáo | Tạo công ty thứ 2, kiểm tra dữ liệu không lẫn |
| Luồng duyệt | Model kế thừa `approval.matrix.mixin` | Submit → approve/refuse/withdraw, kiểm tra `approval_state` và quyền của người không phải owner |
| API ngoài | `pcv_minvoice`, `pcv_mysign`, đồng bộ MySQL | `unittest.mock.patch` hàm gọi HTTP/DB; **không** gọi hệ thống thật |
| Tiền tệ, làm tròn | Tính thuế, tỷ giá, phân bổ | So sánh bằng `currency.compare_amounts`, test cả trường hợp lẻ đồng |

## Chạy test

```bash
docker compose run --rm --entrypoint /usr/bin/odoo odoo \
  -c /etc/odoo/odoo.conf --db_host=db --db_user=odoo --db_password=odoo \
  -d tlip_test -i <module> --test-enable --test-tags /<module> --stop-after-init
```

Chạy một class: `--test-tags /<module>:TestRfpPayment`. Đọc log tìm `FAIL`, `ERROR`; báo kết quả cho người dùng gồm số test chạy, số qua, lỗi đầu tiên nếu có.

## Không được

- Không dùng dữ liệu thật hoặc các file `*.json` ở thư mục gốc làm fixture.
- Không viết test chỉ để "qua"; test phải fail khi chức năng sai.
- Không `commit()` trong test.
