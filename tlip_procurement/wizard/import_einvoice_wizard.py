import base64
import io
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None


class ImportEinvoiceWizard(models.TransientModel):
    _name = 'import.einvoice.wizard'
    _description = 'Import E-Invoice Lines from Excel'

    move_id = fields.Many2one('account.move', string='Invoice', required=True, ondelete='cascade')
    file = fields.Binary(string='Excel File (.xlsx)', required=True)
    filename = fields.Char(string='Filename')

    def action_import(self):
        if not openpyxl:
            raise UserError(_("The 'openpyxl' library is required to import Excel files."))

        try:
            wb = openpyxl.load_workbook(io.BytesIO(base64.b64decode(self.file)))
            ws = wb.active
        except Exception as e:
            raise UserError(_("Cannot read the Excel file: %s") % str(e))

        lines_vals = []
        errors = []

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(cell is not None and str(cell).strip() for cell in row):
                continue

            line_vals, error = self._validate_row(row_idx, row)
            if error:
                errors.append(error)
            else:
                lines_vals.append(line_vals)

        if errors:
            raise UserError("\n".join(errors))

        if not lines_vals:
            raise UserError(_("No valid data rows found in the Excel file."))

        self.env['e.invoice.line'].create(lines_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Successful'),
                'message': _('%d e-invoice line(s) imported successfully.') % len(lines_vals),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _validate_row(self, row_idx, row):
        """Validate a single Excel row and return (line_vals, error_msg).

        Returns (dict, None) on success or (None, str) on validation failure.
        """
        row_data = (list(row) + [None] * 14)[:14]
        invoice_issuer, tax_code, form_no, serial, number, invoice_date, goods_name, uom_name, qty, price_unit, tax_val, price_subtotal, price_tax, price_total = row_data

        # Required fields
        required = {
            'Form No.': form_no,
            'Serial': serial,
            'No': number,
            'Invoice Date': invoice_date,
            'Goods/Service Name': goods_name,
            'UoM ': uom_name,
            'Quantity': qty,
            'Unit Price': price_unit,
            'Tax %': tax_val,
        }
        missing = [label for label, val in required.items() if val is None or str(val).strip() == '']
        if missing:
            return None, _("Row %d: Missing required field(s): %s.") % (row_idx, ', '.join(missing))

        # Invoice date
        if hasattr(invoice_date, 'date'):
            parsed_date = invoice_date.date()
        elif hasattr(invoice_date, 'year'):
            parsed_date = invoice_date
        else:
            try:
                parsed_date = datetime.strptime(str(invoice_date).strip(), '%d/%m/%Y').date()
            except ValueError:
                return None, _("Row %d: Invalid date '%s'. Use DD/MM/YYYY.") % (row_idx, invoice_date)

        # Quantity
        try:
            parsed_qty = float(qty)
        except (ValueError, TypeError):
            return None, _("Row %d: Invalid quantity '%s'. Must be a number.") % (row_idx, qty)

        # Unit Price
        try:
            parsed_price_unit = float(price_unit)
        except (ValueError, TypeError):
            return None, _("Row %d: Invalid unit price '%s'. Must be a number.") % (row_idx, price_unit)

        # Tax
        tax_ids = []
        try:
            taxes = self.env['account.tax'].search([
                ('amount', '=', float(tax_val)),
                ('type_tax_use', 'in', ('purchase', 'all')),
                ('company_id', '=', self.move_id.company_id.id),
            ], limit=1)
            if taxes:
                tax_ids = [taxes.id]
        except (ValueError, TypeError):
            return None, _("Row %d: Invalid tax value '%s'.") % (row_idx, tax_val)

        # Price Subtotal (optional)
        parsed_price_subtotal = False
        if price_subtotal is not None and str(price_subtotal).strip() != '':
            try:
                parsed_price_subtotal = float(price_subtotal)
            except (ValueError, TypeError):
                return None, _("Row %d: Invalid price subtotal '%s'. Must be a number.") % (row_idx, price_subtotal)

        # Price Tax (optional)
        parsed_price_tax = False
        if price_tax is not None and str(price_tax).strip() != '':
            try:
                parsed_price_tax = float(price_tax)
            except (ValueError, TypeError):
                return None, _("Row %d: Invalid price tax '%s'. Must be a number.") % (row_idx, price_tax)

        # Price Total (optional)
        parsed_price_total = False
        if price_total is not None and str(price_total).strip() != '':
            try:
                parsed_price_total = float(price_total)
            except (ValueError, TypeError):
                return None, _("Row %d: Invalid price total '%s'. Must be a number.") % (row_idx, price_total)

        move_id = self.move_id
        vals = {
            'move_id': move_id.id,
            'invoice_issuer': str(invoice_issuer).strip() if invoice_issuer is not None else move_id.partner_id.name,
            'tax_code': str(tax_code).strip() if tax_code is not None else move_id.partner_id.vat,
            'form_no': str(form_no).strip() if form_no is not None else '',
            'serial': str(serial).strip() if serial is not None else '',
            'number': str(number).strip() if number is not None else '',
            'invoice_date': parsed_date,
            'goods_name': str(goods_name).strip() if goods_name is not None else '',
            'product_uom': str(uom_name).strip() if uom_name is not None else '',
            'product_uom_qty': parsed_qty,
            'price_unit': parsed_price_unit,
            'taxes_id': [(6, 0, tax_ids)],
        }
        if parsed_price_subtotal is not False:
            vals['price_subtotal'] = parsed_price_subtotal
        if parsed_price_tax is not False:
            vals['price_tax'] = parsed_price_tax
        if parsed_price_total is not False:
            vals['price_total'] = parsed_price_total
        return vals, None
