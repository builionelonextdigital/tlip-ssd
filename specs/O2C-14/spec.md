---
id: O2C-14
code: O2C No. 14
title: Lỗi mất thông tin khi chọn kỳ hạn phân bổ
status: Draft
ai_level: Trung bình
shared_modules: Không
source: Tracker "Chi tiết task" STT 29 (O2C No. 14); TLIP_O2C_Giai_phap_chi_tiet_va_uoc_luong.docx mục "No. 14 – Lỗi mất thông tin khi chọn kỳ hạn phân bổ"; Meeting Minutes 2026-10-02 mục 2.2 và việc #5; Tai-hien-issue/O2C No.14 (step by step).xlsx
business_approver:
technical_approver:
---

# O2C No. 14 – Lỗi mất thông tin khi chọn kỳ hạn phân bổ

## 1. Bối cảnh / Hiện trạng

- Biên bản khảo sát 02/10/2026 (mục 2.2 Deferred Revenue): "Trong quá trình khảo sát, khi lựa chọn kỳ hạn phân bổ thì thông tin bị mất, do đó A1 cần kiểm tra lại." Biên bản không ghi màn hình nào.
- Tracker / tài liệu giải pháp: "Tái hiện lỗi, sửa và kiểm thử lại. Gửi video hướng dẫn Deferred Revenue sau khi sửa. Cần sửa trước khi làm No. 13." Không đổi field.
- File tái hiện (staging, 30/10/2026) đã thử 3 nơi có thể là "kỳ hạn phân bổ":

| Nơi | Thao tác | Kết quả |
|---|---|---|
| (A) **Date From / Date To trên dòng RFP** | Sửa tay mô tả (và đơn giá với loại không phải thuê), sau đó đổi Date To | **Tái hiện được**: mô tả quay về mô tả mặc định của sản phẩm; với RFP loại không phải thuê, đơn giá nhập tay quay về giá bán của sản phẩm |
| (A') Đầu phiếu RFP | Sửa tay mô tả dòng, sau đó điền Payment Reference | **Tái hiện được**: mô tả dòng quay về mặc định |
| (B) Start Date / End Date chuẩn Odoo trên dòng | Điền Start/End Date | Không tái hiện |
| (C) Form Deferred Revenue (Number of Recognitions, Period length, Model) | Đổi các trường | Không tái hiện với các trường thường; chưa thử chọn Deferred Revenue Model vì staging chưa có mẫu |

- Nguyên nhân sơ bộ (file tái hiện, mục D1): mô tả dòng (`name`) và đơn giá (`price_unit`) là trường tự tính cho phép sửa tay; TLIP đã thêm `date_from`, `date_to`, `move_id.ref`, `move_id.payment_reference`, `move_id.land_plot_id` vào danh sách trường phụ thuộc, nên mỗi lần các trường này đổi, hệ thống tính lại và ghi đè giá trị người dùng đã sửa tay (`tlip_account/models/account_move_line.py`, `_compute_name` và `_compute_price_unit`).
- Hậu quả: PIC/kế toán phải nhập lại, dễ gửi khách RFP/hóa đơn điện tử với mô tả hoặc đơn giá sai (VD 27.500.000 đ thành 1,1 đ trên staging).

## 2. Mục tiêu

Khi PIC/kế toán đổi kỳ (Date From/Date To) hoặc thông tin đầu phiếu trên RFP, mô tả và đơn giá đã sửa tay trên dòng được giữ nguyên; mô tả chưa sửa tay vẫn tự cập nhật như hiện nay. Sau khi sửa, A1 gửi lại video hướng dẫn Deferred Revenue.

## 3. Ngoài phạm vi

- Tự động phân bổ doanh thu 3387 theo Date From – Date To, chuyển TK doanh thu sang 3387, số tiền theo số tháng (thuộc **O2C No. 13**). Hiện tượng A6 trong file tái hiện (TK vẫn 511310, số tiền 1 tháng dù kỳ 3 tháng) không xử lý ở đây.
- Đổi giá trị mặc định 5 kỳ × Years trên form Deferred Revenue (cân nhắc ở No. 13).
- Ẩn/hiện cột Date From/Date To theo loại yêu cầu; cột Area/Quantity cho thuê đất (thuộc **O2C No. 15**).
- Khóa sửa chứng từ sau duyệt (thuộc **O2C No. 23**).
- Không thêm, đổi tên hay xóa field.

## 4. Người dùng và quyền

Hạng mục sửa lỗi, không đổi quyền. Hành vi áp dụng cho mọi người đang được phép sửa dòng RFP nháp.

| Vai trò (group) | Được làm | Không được làm |
|---|---|---|
| PIC tạo RFP | Sửa mô tả, đơn giá, kỳ trên dòng RFP nháp; giá trị sửa tay được giữ | Sửa RFP đã duyệt/đã post (giữ nguyên như hiện tại) |
| Kế toán (`tlip_access_rights.group_tlip_accountant`) | Như PIC trên RFP nháp | Như trên |

## 5. Yêu cầu nghiệp vụ

- **R1.** Đổi Date From hoặc Date To trên dòng RFP **không** ghi đè mô tả dòng mà người dùng đã sửa tay.
- **R2.** Đổi Date From hoặc Date To trên dòng RFP **không** ghi đè đơn giá (Unit Price) mà người dùng đã nhập tay, với mọi loại yêu cầu (thuê và không phải thuê).
- **R3.** Đổi thông tin đầu phiếu (Reference, Payment Reference, lô đất) **không** ghi đè mô tả dòng đã sửa tay.
- **R4.** Nếu mô tả dòng **chưa** bị sửa tay (đang là mô tả tự sinh), khi đổi kỳ hoặc lô đất thì mô tả vẫn được tự sinh lại như hiện nay (gồm phần "từ ngày … đến ngày … (from … to …)" khi có lô đất và đủ kỳ).
- **R5.** Đổi **sản phẩm** trên dòng vẫn tính lại mô tả và đơn giá theo sản phẩm mới, kể cả khi trước đó đã sửa tay (giữ hành vi chuẩn).
- **R6.** Với loại yêu cầu thuê, Unit Price vẫn tự tính = Price × Area khi người dùng đổi Price hoặc Area (giữ hành vi hiện tại); chỉ việc đổi kỳ không được làm thay đổi Unit Price.
- **R7.** Giá trị sửa tay được giữ cả khi người dùng đã Save rồi mở lại RFP và đổi kỳ ở lần sau (không chỉ trong cùng một lần sửa).
- **R8.** Điền Start Date / End Date chuẩn Odoo trên dòng tiếp tục không làm mất mô tả/đơn giá (chống hồi quy).
- **R9.** Xác định với TLIP màn hình đã gặp lỗi trong buổi khảo sát (A, B hay C) và gửi lại video hướng dẫn Deferred Revenue sau khi sửa (sản phẩm bàn giao, không phải code).

## 6. Tiêu chí nghiệm thu (AC)

Dữ liệu giả. Công ty **Công ty A** (VND), khách **Beta**. Sản phẩm thuê nhà xưởng "Ready-built factory rent" có mô tả song ngữ "Tiền thuê nhà xưởng xây sẵn" / "Ready-built factory rent"; sản phẩm "Other service" giá bán 1 đ, mô tả "Dịch vụ khác" / "Other service".

| AC | Cho trước (Given) | Khi (When) | Thì (Then) | Ánh xạ R |
|---|---|---|---|---|
| AC1 | RFP nháp, Request Type RBF (thuê), dòng Ready-built factory rent, Area 2.400, Price 25.000 → Unit Price 60.000.000, Date From 01/11/2026 – Date To 30/11/2026. Mô tả đã sửa thành "Tiền thuê nhà xưởng X3 – 2.400 m² theo PL03/HĐ 08/2025" và đã Save | Đổi Date To thành 31/01/2027, Save | Mô tả vẫn là "Tiền thuê nhà xưởng X3 – 2.400 m² theo PL03/HĐ 08/2025"; Unit Price vẫn 60.000.000 | R1, R7 (TC1) |
| AC2 | Như AC1 (mô tả đã sửa, đã Save) | Điền Payment Reference = "HĐ 08/2025" ở đầu phiếu, Save | Mô tả dòng giữ nguyên bản sửa tay | R3 (TC2) |
| AC3 | Như AC1 | Đổi Reference ở đầu phiếu, Save | Mô tả dòng giữ nguyên bản sửa tay | R3 |
| AC4 | RFP nháp, Request Type Other Request, dòng Other service; mô tả sửa thành "Phí cấp thẻ ra vào theo PL02/HĐ 15/2026", Unit Price nhập tay 25.000.000, VAT 10% (tổng 27.500.000); Date From 01/11/2026 – Date To 30/11/2026; đã Save | Đổi Date To thành 31/01/2027, Save | Mô tả giữ nguyên; Unit Price vẫn 25.000.000; tổng vẫn 27.500.000 | R1, R2, R7 (TC3) |
| AC5 | RFP RBF nháp có lô đất "Lô A1", dòng Ready-built factory rent, **chưa** sửa mô tả, kỳ 01/11/2026 – 30/11/2026 → mô tả tự sinh "Tiền thuê nhà xưởng xây sẵn Lô A1 từ ngày 01/11/2026 đến ngày 30/11/2026 (Ready-built factory rent Lô A1 from 01/11/2026 to 30/11/2026)" | Đổi Date To thành 31/01/2027 | Mô tả tự cập nhật thành "… từ ngày 01/11/2026 đến ngày 31/01/2027 (… from 01/11/2026 to 31/01/2027)" | R4 (TC4) |
| AC6 | Như AC5 (mô tả tự sinh) | Đổi lô đất đầu phiếu sang "Lô B2" | Mô tả tự cập nhật với "Lô B2" | R4 |
| AC7 | RFP RBF nháp **không** có lô đất, mô tả chưa sửa = "Tiền thuê nhà xưởng xây sẵn (Ready-built factory rent)" | Đổi Date To | Mô tả vẫn là mô tả mặc định, không lỗi | R4 |
| AC8 | Như AC1 (mô tả đã sửa) | Đổi sản phẩm của dòng sang Other service | Mô tả đổi theo sản phẩm mới "Dịch vụ khác (Other service)" | R5 (TC5) |
| AC9 | Như AC4 (đơn giá nhập tay 25.000.000) | Đổi sản phẩm của dòng sang sản phẩm khác có giá bán 500.000 | Unit Price đổi theo sản phẩm mới = 500.000 | R5 |
| AC10 | RFP RBF nháp, Area 2.400, Price 25.000 → Unit Price 60.000.000 | Đổi Area thành 3.000 | Unit Price = 75.000.000 (vẫn tự tính) | R6 |
| AC11 | RFP Other Request và RFP RBF với mô tả/đơn giá đã sửa tay | Điền Start Date 01/11/2026 – End Date 31/01/2027 (cột chuẩn Odoo), Save | Mô tả và đơn giá giữ nguyên | R8 (TC6) |
| AC12 | **Công ty B** (pháp nhân thứ hai), RFP Other Request như AC4 | Đổi Date To | Kết quả như AC4; không phụ thuộc dữ liệu của Công ty A | R1, R2 |
| AC13 | RFP đã duyệt hoặc đã post | Người dùng thử đổi Date To | Hành vi khóa sửa giữ nguyên như hiện tại (hạng mục này không mở thêm quyền sửa); mô tả/đơn giá không đổi | R1, R2 |
| AC14 | Đã sửa xong trên môi trường test | A1 chạy lại các bước A1–A5, B1 của file tái hiện trên staging | Không còn hiện tượng mất dữ liệu; có video hướng dẫn Deferred Revenue gửi TLIP | R9 |

Ghi chú làm tròn: đơn giá dạng VND số nguyên, giữ đúng 25.000.000 / 60.000.000, không được trả về 1 đ hay giá trị làm tròn khác.

## 7. Dữ liệu và màn hình bị ảnh hưởng

| Model | Field | Mới / Sửa / Đọc | Ghi chú |
|---|---|---|---|
| `account.move.line` | `name` | Sửa (hành vi tính) | Trường tự tính cho sửa tay; đổi điều kiện tính lại. Không đổi định nghĩa field |
| `account.move.line` | `price_unit` | Sửa (hành vi tính) | Như trên |
| `account.move.line` | `date_from`, `date_to` | Đọc | Field TLIP đã có |
| `account.move.line` | `area`, `leasing_price_unit`, `product_id` | Đọc | Đã có |
| `account.move.line` | `deferred_start_date`, `deferred_end_date` | Đọc | Chuẩn Odoo (kiểm hồi quy AC11) |
| `account.move` | `ref`, `payment_reference`, `land_plot_id`, `invoice_type_id` | Đọc | Đã có |

Module: `tlip_account` (chính). Cần kiểm tra ảnh hưởng tới `tlip_leasing` (tạo dòng RFP kỳ tiếp theo từ dòng cũ với `date_from` = `date_to` + 1 ngày) và `tlip_account_asset` (tạo Deferred Revenue từ Start/End Date khi Submit). Không chạm module dùng chung.

Màn hình: form RFP (Sales › Request for Payment), tab dòng; form Deferred Revenue chỉ để xác nhận không hồi quy. PDF RFP và dữ liệu gửi M-invoice lấy mô tả/đơn giá từ dòng nên hưởng kết quả gián tiếp.

## 8. Ràng buộc

- Tuân thủ `AGENTS.md`. Mức dùng AI **Trung bình**: AI viết khung và test; logic tính lại mô tả/đơn giá TC viết hoặc soát từng dòng.
- Không thêm/đổi tên/xóa field (tracker: "Không đổi field – sửa lỗi"). Nếu plan cần field cờ "đã sửa tay" thì phải quay lại sửa spec trước.
- Không làm thay đổi mô tả/đơn giá của RFP đã có trong dữ liệu thật (không migration ghi đè).
- Phải hoàn thành trước O2C No. 13.

## 9. Câu hỏi mở

Spec **không được Approved** khi còn câu hỏi chưa trả lời.

| # | Câu hỏi | Người trả lời | Trả lời |
|---|---|---|---|
| Q1 | Trong buổi khảo sát 02/10/2026, TLIP gặp lỗi ở màn hình nào: (A) Date From/Date To trên dòng RFP, (B) Start/End Date trên dòng, hay (C) form Deferred Revenue? File tái hiện chỉ tái hiện được ở (A). Nếu là (C) thì phạm vi spec phải đổi. | FC (hỏi TLIP) | |
| Q2 | Nếu là (C) khi chọn **Deferred Revenue Model**: chuẩn Odoo sẽ điền lại số kỳ, độ dài kỳ, tài khoản theo mẫu (ghi đè giá trị đang nhập). TLIP muốn chỉ điền vào trường đang trống, hay chấp nhận ghi đè theo mẫu? | FC | |
| Q3 | Mô tả đã sửa tay mà có chứa kỳ cũ (VD "… từ 01/11/2026 đến 30/11/2026"), khi đổi Date To thì hệ thống để nguyên toàn bộ (người dùng tự sửa) hay phải tự thay phần ngày trong mô tả? Spec hiện đề xuất **để nguyên**. Có cần cảnh báo người dùng không? | FC | |
| Q4 | Đổi sản phẩm thì ghi đè cả mô tả **và** đơn giá đã sửa tay (AC8, AC9) – FC xác nhận đúng mong muốn? | FC | |
| Q5 | Với loại thuê, nếu người dùng sửa tay trực tiếp Unit Price (không qua Price × Area) thì khi đổi Area/Price có được ghi đè không? (Spec hiện giữ hành vi tự tính – R6.) | FC | |
| Q6 | Muốn "khôi phục" mô tả tự sinh sau khi đã sửa tay thì người dùng làm thế nào (xóa trống mô tả, chọn lại sản phẩm…)? Có cần không? | FC | |
| Q7 | RFP tạo tự động từ hợp đồng thuê (`tlip_leasing`) cho kỳ tiếp theo: mô tả dòng mới nên tự sinh theo kỳ mới hay copy mô tả của kỳ trước (kể cả phần sửa tay)? | FC + TC | |
| Q8 | Tracker ghi 1,5 MD, tài liệu giải pháp ghi 2 MD. Chốt số nào? Video hướng dẫn Deferred Revenue có tính trong MD này không, ai làm? | TC / PM | |

## 10. Lịch sử

| Ngày | Người | Thay đổi |
|---|---|---|
| 2026-11-02 | AI | Tạo bản nháp từ tracker, tài liệu giải pháp, biên bản 02/10/2026 và file tái hiện No.14 |
