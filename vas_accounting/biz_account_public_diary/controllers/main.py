# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import werkzeug
from werkzeug.exceptions import InternalServerError

from odoo import http
from odoo.models import check_method_name
from odoo.http import content_disposition, request
from odoo.tools.misc import html_escape

import json


class AccountPublicDiaryController(http.Controller):

    @http.route('/account_public_diary', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, options, file_generator, **kwargs):
        uid = request.uid
        options = json.loads(options)

        report = request.env["account.public.diary.wizard"].with_user(uid).browse(options['report_id'])
        try:
            check_method_name(file_generator)
            generated_file_data = report.dispatch_report_action(options, file_generator)
            file_content = generated_file_data['file_content']
            file_type = generated_file_data['file_type']
            response_headers = self._get_response_headers(file_type, generated_file_data['file_name'], file_content)

            if file_type == 'xlsx':
                response = request.make_response(None, headers=response_headers)
                response.stream.write(file_content)
            else:
                response = request.make_response(file_content, headers=response_headers)

            return response
        except Exception as e:
            se = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            res = request.make_response(html_escape(json.dumps(error)))
            raise InternalServerError(response=res) from e

    def _get_response_headers(self, file_type, file_name, file_content):
        headers = [
            ('Content-Type', request.env['account.report'].get_export_mime_type(file_type)),
            ('Content-Disposition', content_disposition(file_name)),
        ]

        if file_type in ('xml', 'xaf', 'txt', 'csv', 'kvr', 'csv'):
            headers.append(('Content-Length', len(file_content)))

        return headers
