# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _, osv

class AccountReport(models.Model):
	_inherit = 'account.report'

	custom_button = fields.Boolean('Custom button')

	def _init_options_buttons(self, options, previous_options=None):
		super(AccountReport, self)._init_options_buttons(options, previous_options)
		if self.custom_button:
			options['buttons'] = [
            	{'name': _('PDF'), 'sequence': 1, 'action': 'acction_print_pdf', 'file_export_type': _('PDF')},
				{'name': _('XLSX'), 'sequence': 20, 'action': 'export_file', 'action_param': 'export_to_xlsx', 'file_export_type': _('XLSX')},
				{'name': _('Save'), 'sequence': 100, 'action': 'open_report_export_wizard'},
			]

