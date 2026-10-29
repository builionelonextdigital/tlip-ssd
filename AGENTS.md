# AGENTS.md – Quy tắc cho AI làm việc trên repo TLIP

File này dành cho mọi công cụ AI viết code (Claude Code, Cursor, Copilot, Codex...). Claude Code đọc qua `CLAUDE.md`.
Người chịu trách nhiệm cuối cùng về code luôn là TC tạo merge request, không phải AI.

## 1. Dự án

- Odoo **18.0 Enterprise**, image `registry.gitlab.com/portcitiesidealis/odoo-enterprise:18.0`, PostgreSQL 16.
- Khách hàng TLIP gồm **3 pháp nhân** chạy trên cùng một database (multi-company). Dữ liệu giữa các công ty phải tách biệt.
- Code customize ban đầu do Port Cities viết (~33k dòng Python, 22 module). A1 / Rikkei đang tiếp quản và cải tiến theo 2 gói O2C và P2P.
- Tài liệu nghiệp vụ nằm trong `Project-infomations/` (biên bản họp, tài liệu giải pháp, tracker `TLIP_Phase_Tracker.xlsx`, báo cáo audit `TLIP Audit.pdf`). **Chỉ đọc, không sửa** thư mục này.

### Bản đồ module

| Module | Nội dung chính |
|---|---|
| `tlip_base` | Cấu hình nền, partner, job, mail composer |
| `tlip_approval` | `approval.matrix.mixin` – luồng duyệt dùng chung cho ~20 model. **Module dùng chung** |
| `tlip_access_rights` | Nhóm quyền, record rule cho mọi phân hệ. **Module dùng chung** |
| `tlip_account` | RFP (`account.move` có `is_request_payment`), `invoice.type`, Payment, Batch Payment, budget, khóa sổ kỳ, báo cáo |
| `tlip_account_asset` | TSCĐ, Asset Modify CR |
| `tlip_account_report`, `vas_*` | Báo cáo kế toán VAS, công nợ |
| `tlip_procurement` | F1 `request.purchase`, F2 `procurement.task`, `task.order.selection`, hợp đồng `purchase.requisition`, PO |
| `tlip_stock`, `stock_activities_report` | Kho |
| `tlip_leasing` | Hợp đồng thuê, phụ lục |
| `tlip_utilities`, `tlip_synchronization` | Điểm đo điện/nước, đồng bộ chỉ số từ MySQL |
| `tlip_fx_out` | Tỷ giá |
| `tlip_evaluation` | Đánh giá nhà cung cấp |
| `pcv_minvoice`, `pcv_mysign`, `*_sign_ticket` | Hóa đơn điện tử M-invoice, ký số MySign. **Module dùng chung** |
| `queue_job`, `report_xlsx`, `web_*`, `vn_address`, `dynamic_docx_pdf_reports_omax`, `account_report_filter_currency` | Module bên thứ ba / OCA. **Không sửa** |

### Thuật ngữ nghiệp vụ

- **RFP / YCTT** (Request for Payment, Yêu cầu thanh toán): `account.move` với `is_request_payment = True`, loại theo `invoice_type_id`.
- **F1** đề nghị mua sắm, **F2** procurement task, **F3** đề nghị thanh toán phía mua.
- **3387** doanh thu nhận trước (Deferred Revenue); **131** phải thu; **331** phải trả; **335** chi phí trích trước.
- **EPE**: doanh nghiệp chế xuất (tỷ lệ chế xuất / không chế xuất quyết định thuế suất).
- **Kỳ chốt điện nước**: ngày 8, 17 và cuối tháng.
- Mã hạng mục: `O2C No. x`, `P2P No. x` (theo tài liệu giải pháp), `AUDIT #x` (theo báo cáo audit).

## 2. Không được làm

1. **Không đọc hoặc in ra bí mật**: `odoo.conf` (chứa mật khẩu), file `.env`, trường mật khẩu/token của M-invoice, MySign.
2. **Không đọc các file dữ liệu thật** ở thư mục gốc: `cosphi.json`, `electrict.json`, `water.json` (chỉ số đo và mã khách hàng thật).
3. **Không kết nối** database staging/production, không gọi API M-invoice/MySign thật. Trong test phải mock.
4. **Không chạy** `deploy_dev.sh`, `git push`, lệnh xóa database hay volume.
5. **Không sửa** module bên thứ ba (bảng trên) và thư mục `Project-infomations/`.
6. **Không đổi tên hoặc xóa field đang có** nếu tài liệu giải pháp không yêu cầu; dữ liệu thật đang dùng các field đó.

## 3. Quy ước code Odoo 18

- View dùng `<list>` (không dùng `<tree>`); điều kiện hiển thị dùng `invisible="..."`, `readonly="..."`, `required="..."` (không dùng `attrs`, `states`).
- `create` dùng `@api.model_create_multi`.
- Model có `company_id`: đặt `_check_company_auto = True` và `check_company=True` cho Many2one liên quan. Mọi truy vấn và báo cáo phải lọc theo công ty.
- Default ngày giờ dùng lambda hoặc callable: `default=lambda self: fields.Datetime.now()`. **Không** viết `def f(self, date_from=fields.Datetime.now())` (lỗi AUDIT #11).
- So sánh tiền: `currency.compare_amounts`, `currency.is_zero`, `float_compare`. Không so float trực tiếp.
- SQL: dùng `odoo.tools.SQL` hoặc tham số `%s`. **Không** f-string ghép SQL.
- Không dùng `eval`; dùng `ast.literal_eval` hoặc `safe_eval`.
- Gọi HTTP ra ngoài luôn có `timeout=(5, 30)`.
- `sudo()` chỉ dùng khi bắt buộc, kèm comment giải thích lý do và giới hạn bản ghi.
- Các context key bỏ qua kiểm tra (`force_post`, `bypass_period_closing`, `skip_accounting_period_check`) chỉ được chấp nhận với nhóm kế toán trưởng hoặc khi gọi trong `sudo()` nội bộ (AUDIT #19).
- Model kế thừa `approval.matrix.mixin`: không ghi trực tiếp `approval_state`/`state` từ UI hay RPC; đi qua hàm duyệt của mixin. Chứng từ đã duyệt hoặc đã post không được sửa số tiền, đối tác, dòng.
- Code, comment, tên biến bằng tiếng Anh. Chuỗi hiển thị viết tiếng Anh và bổ sung bản dịch trong `i18n/vi_VN.po`.

## 4. Mỗi thay đổi phải có

1. **Test** trong `<module>/tests/` (xem skill `odoo-test`). Hiện repo chưa có test cho module `tlip_*`, nên mọi hạng mục mới đều bắt đầu bằng việc tạo test.
2. **Quyền**: model mới có dòng trong `security/ir.model.access.csv`, **luôn có group** (dòng không group = mọi user, kể cả portal – AUDIT #10).
3. **Version** trong `__manifest__.py` tăng theo dạng `18.0.x.y.z`; thêm script trong `migrations/` nếu đổi dữ liệu có sẵn.
4. **Bản dịch** vi_VN cho chuỗi mới.
5. **Commit message** bắt đầu bằng mã hạng mục: `[O2C No. 1] Post RFP when payment is confirmed`.

## 5. Mức dùng AI theo hạng mục

Tracker `Project-infomations/TLIP_Phase_Tracker.xlsx`, tab "Chi tiết task", cột **Mức dùng AI**:

- **Cao**: AI được sinh code và test; TC đọc lại toàn bộ.
- **Trung bình**: AI viết khung (field, view, security, test); logic nghiệp vụ TC viết hoặc soát từng dòng.
- **Thấp** (kế toán, tỷ giá, 3387, phân bổ FIFO, tích hợp M-invoice): **AI không viết logic lõi**. AI chỉ đọc code cũ, giải thích, viết test theo ví dụ số liệu của FC và đề xuất kế hoạch.

Khi được giao một hạng mục, hỏi mã hạng mục và mức dùng AI trước nếu chưa biết.

## 6. Module dùng chung

Thay đổi trong `tlip_approval`, `tlip_access_rights`, `pcv_minvoice`, `pcv_mysign` ảnh hưởng cả O2C và P2P.
Phải ghi rõ trong merge request và cần **pod Core review** (xem skill `shared-module-review`). Chạy test của các module phụ thuộc trước khi mở merge request.

## 7. Chạy và kiểm tra

Lệnh tham khảo (kiểm tra lại với môi trường dev của team):

```bash
# Cài/cập nhật module và chạy test trên database test riêng
docker compose run --rm --entrypoint /usr/bin/odoo odoo \
  -c /etc/odoo/odoo.conf --db_host=db --db_user=odoo --db_password=odoo \
  -d tlip_test -i <module> --test-enable --test-tags /<module> \
  --stop-after-init --without-demo=False
```

Báo cáo lại cho người dùng bằng **tiếng Việt**: đã sửa file nào, test nào đã chạy và kết quả, điểm nào cần TC/FC xác nhận.
