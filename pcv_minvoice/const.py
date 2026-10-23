MINVOICE_TOKEN_EXPIRE_HOURS = 8

MINVOICE_TYPE_SELECTION = [
    ("01GTKT", "Hóa đơn điện tử giá trị gia tăng (TT32)"),
    ("02GTTT", "Hóa đơn bán hàng - (TT32)"),
    ("07KPTQ", "Hóa đơn bán hàng (dành cho tổ chức, cá nhân trong khu phi thuế quan) - (TT32)"),
    ("03XKNB", "Phiếu xuất kho kiêm vận chuyển hàng nội bộ - (TT32)"),
    ("04HGDL", "Phiếu xuất kho gửi bán hàng đại lý - (TT32)"),
    ("01BLP", "Biên lai thu phí, lệ phí - (TT32)"),
    ("1", "Hóa đơn giá trị gia tăng (TT78)"),
    ("2", "Hóa đơn bán hàng (TT78)"),
    ("3", "Hóa đơn bán tài sản công (TT78)"),
    ("4", "Hóa đơn bán hàng dự trữ quốc gia (TT78)"),
    ("5", "Tem điện tử, vé điện tử, thẻ điện tử, phiếu thu điện tử hoặc các chứng từ điện tử theo quy định tại NĐ 123 (TT78)"),
    ("6", "Phiếu xuất kho kiêm vận chuyển nội bộ điện tử, phiếu xuất kho hàng gửi bán đại lý điện tử (TT78)"),
    ("7", "Hóa đơn bán hàng dành cho tổ chức, cá nhân trong khu phi thuế quan (TT78)"),
    ("8", "Biên lai thu phí, lệ phí (TT78)"),
]

MINVOICE_TYPE_TT32 = ["01GTKT", "02GTTT", "07KPTQ", "03XKNB", "04HGDL", "01BLP"]
MINVOICE_TYPE_TT78 = ["1", "2", "3", "4", "5", "6"]

PAYMENT_METHOD_SELECTION = [
    ('TM/CK', 'TM/CK'),
    ('cash', 'Tiền mặt'),
    ('transfer', 'Chuyển khoản')
]
MINVOICE_SAVE_INVOICE_ENDPOINT = "/api/InvoiceApi78/Save"
MINVOICE_SAVE_AND_SIGN_INVOICE_ENDPOINT = "/api/InvoiceApi78/SaveSign"
MINVOICE_SIGN_INVOICE_ENDPOINT = "/api/InvoiceApi78/Sign"
MINVOICE_ADJUST_INVOICE_ENDPOINT = "/api/InvoiceApi78/DieuChinhSaveSign"
MINVOICE_REPLACE_INVOICE_ENDPOINT = "/api/InvoiceApi78/ThayTheSaveSign"
MINVOICE_CANCEL_INVOICE_ENDPOINT = "/api/InvoiceApi78/HuyHoaDon"
MINVOICE_VIEW_INVOICE_PRINT_ENDPOINT = "/api/InvoiceApi78/PrintInvoice"
MINVOICE_GET_INVOICE_TEMPLATES_ENDPOINT = "/api/Invoice68/GetTypeInvoiceSeries"
MINVOICE_SEND_EMAIL_ENDPOINT = "/api/Invoice68/SendEmailMulti"
MINVOICE_GET_INVOICE_STATUS_ENDPOINT = "/api/InvoiceApi78/GetInfoInvoice"
