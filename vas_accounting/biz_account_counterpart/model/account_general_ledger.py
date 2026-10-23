from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'



    def _init_options_buttons(self, options, previous_options=None):
        super(GeneralLedgerCustomHandler, self)._init_options_buttons()
        options['buttons'] = [
            {'name': _('PDF'), 'sequence': 10, 'action': 'export_file', 'action_param': 'export_to_pdf', 'file_export_type': _('PDF')},
            {'name': _('XLSX'), 'sequence': 20, 'action': 'export_file', 'action_param': 'export_to_xlsx', 'file_export_type': _('XLSX')},
            {'name': _('S03b-DN (XLSX)'), 'sequence': 30, 'action': 'export_file', 'action_param': 'export_to_xlsx', 'file_export_type': _('XLSX')},
            {'name': _('S03b-DN (PDF)'), 'sequence': 10, 'action': 'export_file', 'action_param': 'export_to_pdf', 'file_export_type': _('PDF')},
            {'name': _('Save'), 'sequence': 100, 'action': 'open_report_export_wizard'},
        ]


