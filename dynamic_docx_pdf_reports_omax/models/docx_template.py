# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
from PIL import Image
import io
import docx
import os
import logging
from python_docx_replace import docx_get_keys
from python_docx_replace import docx_replace
# import datetime
from odoo.addons.website.tools import text_from_html
import copy
from docx.table import _Cell
from docx.shared import Inches, Pt
import html2text
import platform

_logger = logging.getLogger(__name__)


class DocxTemplate(models.Model):
    _name = 'docx.template'
    _description = "Docx Template"

    name = fields.Char(string='Report Name', required=True)
    model_id = fields.Many2one(
        "ir.model", string='Model', required=True, ondelete="cascade")
    docx_file = fields.Binary(string='Upload File', required=True)
    ir_actions_server_id = fields.Many2one(
        "ir.actions.server", string="Action Server")
    new_docx_file = fields.Binary(string='Upload File.', required=False)
    file_name = fields.Char(string='File Name', size=256)
    font_name = fields.Char(string='Font Name', size=256)
    font_size = fields.Integer(string='Font Size', default=10)
    print_type = fields.Selection(selection=[
        ('docx', 'DOCX'),
        ('pdf', 'PDF'),
    ], string='Report type', default='docx', required=True)  # , tracking=True
    skip_wizard = fields.Boolean(string='skip print pop-up')
    field_ids = fields.One2many('ir.model.fields', related='model_id.field_id')

    def create(self, vals):
        res = super(DocxTemplate, self).create(vals)
        fname = str(res.file_name.split('.')[-1])
        if fname != 'docx':
            raise UserError(_('Please choose the file with .docx extension!'))
        model_id = res.model_id
        docx_template = self.env["ir.model"].search(
            [('model', '=', 'docx.template')])
        code_with_ctx = "action = model.with_context(menu_action_id=" + str(
            res.id) + ").make_docx_pdf_report()"
        values = {
            'name': str(res.name),
            'type': 'ir.actions.server',
            'model_id': docx_template.id,
            'binding_model_id': model_id.id,
            'binding_view_types': 'form',  # 'form,list'
            'binding_type': 'action',
            'state': 'code',
            'groups_id': [(4, self.env.ref('dynamic_docx_pdf_reports_omax.group_dynamic_docx_report_user').id)],
            # 'code':'action = model.make_docx_pdf_report()',
            'code': code_with_ctx,
        }
        action_id = self.env['ir.actions.server'].create(values)
        res.ir_actions_server_id = action_id
        return res

    def write(self, values):
        if 'model_id' in values and self.ir_actions_server_id:
            raise UserError(_('You can not change Model.'))
        res = super(DocxTemplate, self).write(values)
        fname = str(self.file_name.split('.')[-1])

        if fname != 'docx':
            raise UserError(_('Please choose the file with .docx extension!'))
        if 'name' in values:
            if self.ir_actions_server_id:
                self.ir_actions_server_id.name = self.name
        return res

    def unlink(self):
        if self.ir_actions_server_id:
            self.ir_actions_server_id.unlink()
        return super(DocxTemplate, self).unlink()

    def get_image(self, paragraph, value):
        image = Image.open(value).convert("RGBA")
        image.save('/tmp/out.png')
        run = paragraph.add_run()
        # run.add_picture('/tmp/out.png')
        run.add_picture('/tmp/out.png', width=Inches(1), height=Inches(1))

    def make_docx_pdf_report(self, download=True):
        self = self.sudo()
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(active_ids)
        ###
        menu_action_id = False
        if 'menu_action_id' in list(self._context.keys()):
            menu_action_id = int(self._context.get('menu_action_id'))
        ###
        if active_model and menu_action_id:
            model_id = self.env["ir.model"].search(
                [('model', '=', active_model)])
            docx_template_id = self.browse(menu_action_id)
            if docx_template_id:
                # existing file read
                val = base64.b64decode(docx_template_id.docx_file)
                with open('/tmp/output.docx', 'wb') as autfile:
                    autfile.write(val)
                    autfile.close()

                for rec in records:
                    doc = docx.Document("/tmp/output.docx")
                    for doc_style in doc.styles:
                        if 'font' in dir(doc_style):
                            if docx_template_id.font_name:
                                doc_style.font.name = str(
                                    docx_template_id.font_name)
                            if docx_template_id.font_size != 0:
                                doc_style.font.size = Pt(
                                    docx_template_id.font_size)
                    # Table code
                    row_number = False
                    for table in doc.tables:
                        row_number = 0
                        del_row_number = False
                        ##
                        last_added_rows = []  # after o2m add remaining lines of tbl
                        need_update_index = False  # execute o2m then is true
                        new_lines = []  # o2m lines store
                        ##
                        for row in table.rows:
                            ###
                            if need_update_index:
                                new_row = copy.deepcopy(
                                    table._tbl.tr_lst[row_number])
                                if table._tbl.tr_lst[row_number] in new_lines and row_number > 1:
                                    new_row = self.copy_last_added_rows(
                                        table._tbl.tr_lst, new_lines, row_number)
                                for tc in new_row.tc_lst:
                                    cell = _Cell(tc, new_row.tc_lst)
                                last_added_rows.append(new_row)
                            ###
                            column_names = []
                            lines = False
                            for cell in row.cells:
                                if '$' in str(cell.text):
                                    split_vals = str(cell.text).split('$')
                                    main_field = split_vals[1]
                                    sub_split_vals = ''
                                    if '.' in split_vals[1]:
                                        sub_split_vals = str(
                                            split_vals[1]).split('.')
                                        main_field = sub_split_vals[0]
                                        sub_split_vals.remove(main_field)
                                    Model = self.env["ir.model"]
                                    Fields = self.env["ir.model.fields"]
                                    model_id = Model.search(
                                        [('model', '=', active_model)])
                                    get_field = Fields.search(
                                        [('name', '=', str(main_field)), ('model_id', '=', model_id.id)])
                                    if get_field:
                                        if get_field.ttype == 'one2many':
                                            lines = rec[get_field.name]
                                            # make list of table columns
                                            if not column_names:
                                                column = len(row.cells)
                                                for i in range(1, column + 1):
                                                    for cell in row.cells:
                                                        new_cell = cell
                                                        if '$'+str(main_field)+'.' in str(new_cell.text):
                                                            split_vals = str(new_cell.text).split(
                                                                '$'+str(main_field)+'.')
                                                            split_vals = '$' + \
                                                                split_vals[1]
                                                            column_names.append(
                                                                split_vals)
                                                        else:  # also add blank column too
                                                            column_names.append(
                                                                new_cell.text)
                                                    del_row_number = row_number
                                                    break
                                            if lines:
                                                need_update_index = True
                                        else:
                                            use_existing = True
                                            if need_update_index:
                                                pass
                                            else:
                                                res_value = self.get_value_func(
                                                    rec, active_model, cell.text)
                                                if str(type(res_value)) == "<class '_io.BytesIO'>":
                                                    # add img in normal table
                                                    paragraph = cell.paragraphs[0]
                                                    for p in paragraph.runs:
                                                        p.text = ''  # remove text
                                                    self.get_image(
                                                        paragraph, res_value)  # add img
                                                else:
                                                    if res_value:
                                                        cell.text = str(
                                                            res_value)
                                                    else:
                                                        cell.text = ''
                                    else:
                                        cell.text = str(
                                            cell.text) + " " + "Wrong field"
                            if need_update_index and not lines:  # not get_field
                                table_element = table._tbl
                                row_element = row._tr
                                for tc in row_element.tc_lst:
                                    cell = _Cell(tc, row_element.tc_lst)
                                table_element.remove(row_element)
                                row_number -= 1
                            if lines:
                                # remove technical name field
                                # ex.$order_line.product_id,$order_line.name,$order_line.product_uom_qty,$order_line.tax_id...
                                if del_row_number == row_number:
                                    use_existing = True
                                    table_element = table._tbl
                                    row_element = row._tr
                                    table_element.remove(row_element)
                                    row_number -= 1

                                for line in lines:
                                    line_model = line._name
                                    i = 0
                                    # row_cells = table.add_row().cells#add new lines
                                    new_row = table.add_row()
                                    row_cells = new_row.cells
                                    new_lines.append(new_row._tr)
                                    for column_name in column_names:
                                        res_value = self.get_value_func(
                                            line, line_model, column_name)
                                        if str(type(res_value)) == "<class '_io.BytesIO'>":
                                            # add img in o2m table
                                            image = Image.open(
                                                res_value).convert("RGBA")
                                            image.save('/tmp/out1.png')
                                            paragraph = row_cells[i].paragraphs[0]
                                            run = paragraph.add_run()
                                            # set size of img cell in o2m table
                                            from docx.shared import Inches
                                            row_cells[i].width = Inches(3)
                                            row_cells[i].height = Inches(2)
                                            ###
                                            # add img in cell
                                            run.add_picture(
                                                '/tmp/out1.png', width=Inches(1), height=Inches(1))
                                        else:
                                            if res_value:
                                                # add value of new line's cell
                                                row_cells[i].text = str(
                                                    res_value)
                                            else:
                                                row_cells[i].text = ''
                                        i += 1
                                    use_existing = False
                                # lines = False
                            # else:
                            row_number += 1
                        if last_added_rows:  # add rows after o2m
                            for new_row in last_added_rows:
                                i = 0
                                row_cells = table.add_row().cells
                                # print("\n\n")
                                for tc in new_row.tc_lst:
                                    cell = _Cell(tc, new_row.tc_lst)
                                    # print("cell.text",cell.text)
                                    res_value = self.get_value_func(
                                        rec, active_model, cell.text)
                                    if str(type(res_value)) == "<class '_io.BytesIO'>":
                                        # add img after o2m table
                                        image = Image.open(
                                            res_value).convert("RGBA")
                                        image.save('/tmp/out.png')
                                        paragraph = row_cells[i].paragraphs[0]
                                        run = paragraph.add_run()
                                        # set size of img cell in o2m table
                                        from docx.shared import Inches
                                        cell.width = Inches(3)
                                        cell.height = Inches(2)
                                        ###
                                        # add img in cell
                                        run.add_picture(
                                            '/tmp/out.png', width=Inches(1.5), height=Inches(1.5))
                                    else:
                                        if res_value:
                                            row_cells[i].text = str(res_value)
                                        else:
                                            row_cells[i].text = ''
                                    i += 1
                    # fnsh Table code
                    # get all keys in doc ${payment_term_id}, syntx = ${}
                    keys = docx_get_keys(doc)
                    # print("keys==>",keys)
                    my_dict = {}  # make custom-dict with value
                    for k in keys:
                        key = '$'+str(k)
                        value = self.get_value_func(rec, active_model, key)
                        my_dict[str(k)] = value
                    docx_replace(doc, **my_dict)  # default package
                    # self.docx_replace(doc, my_dict)#use custom b'cz of binary field
                    doc.save("/tmp/final.docx")
                    input_file = '/tmp/final.docx'
                    output_file = '/tmp/final.pdf'
                    # os.system(
                    #    f"soffice --headless --convert-to pdf --outdir {os.path.dirname(os.path.realpath(output_file))} {input_file}")  # save as pdf

                    os_name = platform.system()
                    try:
                        if os_name == 'Linux':
                            os.system(
                                f"libreoffice --headless --convert-to pdf /tmp/final.docx --outdir /tmp")
                        else:
                            os.system(
                                f"soffice --headless --convert-to pdf:writer_pdf_Export C:/tmp/final.docx --outdir {output_file}")
                    except Exception as err:
                        _logger.error(
                            f"\n\n An Exception occured: {str(err)}\n\n")
                if docx_template_id.skip_wizard or self._context.get('skip_wizard'):
                    docx_value = {
                        'name': docx_template_id.name,
                        'print_type': docx_template_id.print_type,
                    }
                    docx_template_wiz = self.env['docx.template.wiz'].create(
                        docx_value)
                    return docx_template_wiz.with_context(docx_template_id=docx_template_id.id).download_file(download)
                else:
                    return {
                        'name': _('Download or Attach Report'),
                        'res_model': 'docx.template.wiz',
                        'view_mode': 'form',
                        'context': {
                            'default_name': docx_template_id.name,
                            'default_print_type': docx_template_id.print_type,
                            'docx_template_id': docx_template_id.id,
                        },
                        'target': 'new',
                        'type': 'ir.actions.act_window',
                    }

    def get_value_func(self, rec, active_model, cell_value):  # record,model_name, value
        res_value = False
        if '$' in str(cell_value):
            split_vals = str(cell_value).split('$')
            main_field = split_vals[1]
            # check sub field name exist or not partner_id.name
            sub_split_vals = ''
            if '.' in split_vals[1]:
                sub_split_vals = str(split_vals[1]).split('.')
                main_field = sub_split_vals[0]
                sub_split_vals.remove(main_field)
            Model = self.env["ir.model"]
            Fields = self.env["ir.model.fields"]

            model_id = Model.search([('model', '=', active_model)])
            get_field = Fields.search(
                [('name', '=', str(main_field)), ('model_id', '=', model_id.id)])
            if get_field:
                if sub_split_vals:
                    parent_model = rec[get_field.name]
                    model_id = Model.search(
                        [('model', '=', parent_model._name)])
                    # for sub_split_val in sub_split_vals:
                    while len(sub_split_vals):
                        sub_split_val = sub_split_vals[0]
                        get_field = Fields.search(
                            [('name', '=', str(sub_split_val)), ('model_id', '=', model_id.id)])
                        sub_split_vals.remove(sub_split_val)
                        if get_field and not sub_split_vals:
                            if get_field.ttype == 'many2one':
                                if parent_model[get_field.name]:
                                    res_value = parent_model[get_field.name].display_name
                                else:
                                    res_value = ''
                            elif get_field.ttype == 'selection':
                                selection_id = get_field.selection_ids.filtered(
                                    lambda r: r.value == parent_model[get_field.name])
                                res_value = selection_id.name
                            elif get_field.ttype == 'many2many':
                                res_value = ', '.join(
                                    map(lambda x: x.name, parent_model[get_field.name]))
                            elif get_field.ttype == 'boolean':
                                if parent_model[get_field.name]:
                                    res_value = 'Yes'
                                else:
                                    res_value = 'No'
                            elif get_field.ttype == 'binary':
                                res_value = parent_model[get_field.name]
                                if res_value:
                                    res_value = io.BytesIO(
                                        base64.b64decode(res_value))
                            elif get_field.ttype == 'float':
                                res_value = parent_model[get_field.name]
                            elif get_field.ttype == 'integer':
                                res_value = parent_model[get_field.name]
                            elif get_field.ttype == 'text':
                                if parent_model[get_field.name]:
                                    res_value = parent_model[get_field.name]
                                else:
                                    res_value = ''
                            elif get_field.ttype == 'monetary':
                                if rec.currency_id.position == 'before':
                                    res_value = str(
                                        rec.currency_id.symbol) + str(parent_model[get_field.name])
                                else:
                                    res_value = str(
                                        parent_model[get_field.name]) + str(rec.currency_id.symbol)
                            elif get_field.ttype == 'html':
                                if parent_model[get_field.name]:
                                    # res_value = text_from_html(parent_model[get_field.name])
                                    res_value = html2text.html2text(
                                        parent_model[get_field.name])
                                else:
                                    res_value = ''
                            else:
                                if parent_model[get_field.name]:
                                    res_value = parent_model[get_field.name]
                                else:
                                    res_value = ''
                        if get_field and sub_split_vals:
                            parent_model = parent_model[get_field.name]
                            model_id = Model.search(
                                [('model', '=', parent_model._name)])
                else:  # not sub field
                    # print("get_field.ttype==>>",get_field.ttype)
                    if get_field.ttype == 'many2one':
                        if rec[get_field.name]:
                            res_value = rec[get_field.name].display_name
                        else:
                            res_value = ''
                    elif get_field.ttype == 'selection':
                        selection_id = get_field.selection_ids.filtered(
                            lambda r: r.value == rec[get_field.name])
                        res_value = selection_id.name
                    elif get_field.ttype == 'many2many':
                        res_value = ', '.join(
                            map(lambda x: x.name, rec[get_field.name]))
                    elif get_field.ttype == 'boolean':
                        if rec[get_field.name]:
                            res_value = 'Yes'
                        else:
                            res_value = 'No'
                    elif get_field.ttype == 'binary':
                        res_value = rec[get_field.name]
                        if res_value:
                            res_value = io.BytesIO(base64.b64decode(res_value))
                    elif get_field.ttype == 'float':
                        res_value = rec[get_field.name]
                    elif get_field.ttype == 'integer':
                        res_value = rec[get_field.name]
                    elif get_field.ttype == 'text':
                        if rec[get_field.name]:
                            res_value = rec[get_field.name]
                        else:
                            res_value = ''
                    elif get_field.ttype == 'monetary':
                        if rec.currency_id.position == 'before':
                            res_value = str(rec.currency_id.symbol) + \
                                str(rec[get_field.name])
                        else:
                            res_value = str(
                                rec[get_field.name]) + str(rec.currency_id.symbol)
                    elif get_field.ttype == 'html':
                        if rec[get_field.name]:
                            # res_value = text_from_html(rec[get_field.name])
                            res_value = html2text.html2text(
                                rec[get_field.name])
                            # print("res_value===>>",res_value,type(res_value))
                        else:
                            res_value = ''
                    else:
                        if rec[get_field.name]:
                            res_value = rec[get_field.name]
                        else:
                            res_value = ''
            else:  # not found field
                res_value = str(cell_value) + " " + "Wrong field"
        else:
            res_value = cell_value
        return res_value

    def copy_last_added_rows(self, table_row_list, new_lines, row_number):
        for i in range(1, len(table_row_list)):
            if table_row_list[row_number] in new_lines:
                row_number -= 1
            else:
                return table_row_list[row_number]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
