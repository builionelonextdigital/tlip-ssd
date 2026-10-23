# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import base64


class DocxTemplateWiz(models.TransientModel):
    _name = "docx.template.wiz"
    _description = "docx.template.wiz"

    print_type = fields.Selection(selection=[
        ('docx', 'DOCX'),
        ('pdf', 'PDF'),
    ], default='docx', required=True)
    name = fields.Char("Report File Name", size=64, readonly=True)
    attachment = fields.Boolean(string='Attachment', default=False)

    def download_file(self, download=True):
        docx_id = self.env.context.get('docx_template_id')
        docx_template_id = self.env["docx.template"].browse(docx_id)
        file = False
        filename = False
        mime_type = False
        if self.print_type == 'pdf':
            file = open("/tmp/final.pdf", "rb")
            filename = f"{str(docx_template_id.name)}.pdf"
            mime_type = 'application/pdf'
        if self.print_type == 'docx':
            file = open("/tmp/final.docx", "rb")
            filename = f"{str(docx_template_id.name)}.docx"
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        if file and filename:
            file_data = file.read()
            out = base64.encodebytes(file_data)
        docx_template_id.write({'new_docx_file': out})
        if mime_type and self.attachment:
            active_model = self._context.get('active_model')
            active_id = self._context.get('active_id')
            # active_id
            attachment = self.env['ir.attachment'].sudo().create({
                'name': filename,
                'type': 'binary',
                'datas': out,
                'mimetype': mime_type,
                'res_model': active_model,
                'res_id': active_id,
            })
            return {'type': 'ir.actions.act_window_close'}

        if download:
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=docx.template&download=true&field=new_docx_file&id=%s&filename=%s' % (docx_template_id.id, filename),
                # 'target': 'self',
                'target': 'new',
            }
        else:
            return docx_template_id.new_docx_file
