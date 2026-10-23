from odoo.tools import config, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import base64
import csv
import io
import logging
import tempfile
from openpyxl import load_workbook
import openpyxl.cell.cell as types
import openpyxl.styles.numbers as styles  # noqa: PLC0415
from odoo import _, fields
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import request

ALL_ERRORS = (
    AccessDenied,
    AccessError,
    Exception,
    MissingError,
    IndexError,
    UserError,
    ValidationError,
    ValueError,
)

_logger = logging.getLogger(__name__)

try:
    import xlrd
    import xlwt
except (ImportError, IOError) as err:
    _logger.error(err)


# Handle XLSX
def read_xlsx(base64_string):
    # Decode the base64 string
    file_data = base64.b64decode(base64_string)

    # Write the data to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
        tmp_file.write(file_data)
        tmp_file_path = tmp_file.name
    book = load_workbook(tmp_file_path)
    sheets = book.sheetnames
    sheet_name = sheets[0]
    sheet = book[sheet_name]
    rows = []
    for rowx, row in enumerate(sheet.rows, 1):
        values = []
        for colx, cell in enumerate(row, 1):
            if cell.data_type is types.TYPE_ERROR:
                raise ValueError(
                    _("Invalid cell value at row %(row)s, column %(col)s: %(cell_value)s",
                      row=rowx, col=colx, cell_value=cell.value)
                )

            if cell.value is None:
                values.append('')
            elif isinstance(cell.value, float):
                if cell.value % 1 == 0:
                    values.append(str(int(cell.value)))
                else:
                    values.append(str(cell.value))
            elif cell.is_date:
                d_fmt = styles.is_datetime(cell.number_format)
                if d_fmt == "datetime":
                    values.append(cell.value.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT))
                elif d_fmt == "date":
                    values.append(cell.value.strftime(
                        DEFAULT_SERVER_DATE_FORMAT))
                else:
                    raise ValueError(
                        _("Invalid cell format at row %(row)s, column %(col)s: %(cell_value)s, with format: %(cell_format)s, as (%(format_type)s) formats are not supported.",
                          row=rowx, col=colx, cell_value=cell.value, cell_format=cell.number_format, format_type=d_fmt)
                    )
            else:
                values.append(str(cell.value))

        if any(x.strip() for x in values):
            rows.append(values)
    return sheet, rows


# Handle CSV, XLS
def get_sheet(imported_file, sheet_index=0, sheet_name=False, filename=None):
    if filename and filename.endswith(".csv"):
        import_file_datas = base64.b64decode(imported_file)
        data = io.StringIO(import_file_datas.decode("utf-8"))
        data.seek(0)
        workbook = xlwt.Workbook(filename[:-4] + ".xlsx")
        worksheet = workbook.add_sheet("data")
        for r, row in enumerate(csv.reader(data)):
            for c, col in enumerate(row):
                worksheet.write(r, c, col)
        xlsx_buffer = io.BytesIO()
        workbook.save(xlsx_buffer)
        imported_file_binary = xlsx_buffer.getvalue()
    else:
        imported_file_binary = base64.b64decode(imported_file)

    book = xlrd.open_workbook(file_contents=imported_file_binary)
    if sheet_name:
        sheet = book.sheet_by_name(sheet_name)
    else:
        sheet = book.sheet_by_index(sheet_index)
    return sheet
