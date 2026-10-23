# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

SAMPLE_CASHFLOW_DATA = {
    '01': [{
        'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128'],
        'reciprocal_account_import_ids': ['121', '1211', '1212', '1218', '131', '1311', '1312', '5111', '5112', '5113',
                                          '5114', '5117', '5118', '515', '5151', '5152', '5153', '5154', '5155',
                                          '5158'],
        'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
    }],
    '02': [{
        'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
        'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128', '1129'],
        'reciprocal_account_export_ids': ['331'],
        'diary_book_ids': []
    }],
    '03': [{
        'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
        'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128', '1129'],
        'reciprocal_account_export_ids': ['3341', '33411', '33412', '3348'],
        'diary_book_ids': []
    }],
    '04': [{
        'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
        'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128', '1129', '113', '1131',
                                      '1132'],
        'reciprocal_account_export_ids': ['242', '2421', '2422', '2423', '2428', '335', '3351', '3352', '3353', '3354',
                                          '3358', '635', '6351', '6352', '6353', '6354', '6358'],
        'diary_book_ids': []
    }],
    '05': [{
        'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
        'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128', '1129', '113', '1131',
                                      '1132'],
        'reciprocal_account_export_ids': ['3334'],
        'diary_book_ids': []
    }],
    '06': [{
        'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128', '1129'],
        'reciprocal_account_import_ids': ['133', '1331', '13311', '13312', '1332', '13321', '13322', '141', '1411',
                                          '1412', '244', '2441', '2442', '711', '7111', '7112', '7118'],
        'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
    }],
    '07': [{
        'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
        'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128', '1129', '113', '1131',
                                      '1132'],
        'reciprocal_account_export_ids': ['1611', '1612', '244', '2441', '2442', '33311', '33312', '3332', '3333',
                                          '33331', '33332', '3334', '3335', '3336', '3337', '33381', '33382', '3339',
                                          '3381', '3382', '3383', '3384', '3385', '3386', '3387', '3388', '33881',
                                          '33882', '33883', '33884', '33885', '344', '3521', '3522', '3523', '3524',
                                          '35241', '35242', '3531', '3532', '3533', '3534', '3561', '3562', '811',
                                          '8111', '8112', '8118'],
        'diary_book_ids': []
    }],
    '21': [{
        'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
        'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112', '1121',
                                      '11210', '11211', '11212', '11213', '11214', '11215', '11216', '11218', '11219',
                                      '1122', '11221', '11221 TGNH USD - NH ACB', '11222', '11223', '11224', '11226',
                                      '11227', '11229', '1123', '11230', '11231', '11232', '11233', '11235', '11236',
                                      '11237', '11238', '1124', '1125', '1126', '1127', '1128', '1129', '113', '1131',
                                      '1132', '331', '3411', '34111', '34112'],
        'reciprocal_account_export_ids': ['2111', '2112', '2113', '2114', '2115', '2118', '2131', '2132', '2133',
                                          '2134', '2135', '2136', '2138', '217', '2171', '2172', '2173', '2174', '2411',
                                          '2412', '2413'],
        'diary_book_ids': []
    }],
    '22': [
        {
            'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_import_ids': ['131', '1311', '1312', '5117', '711', '7111', '7112', '7118'],
            'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
        },
        {
            'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
            'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_export_ids': ['632', '6321', '6322', '811', '8111', '8112', '8118'],
            'diary_book_ids': []
        }
    ],
    '23': [
        {
            'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
            'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_export_ids': ['128', '1281', '1282', '1283', '1288', '171'],
            'diary_book_ids': []
        }
    ],
    '24': [
        {
            'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_import_ids': ['128', '1281', '1282', '1283', '1288', '171'],
            'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
        }
    ],
    '25': [
        {
            'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
            'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_export_ids': ['221', '222', '2281', '331'],
            'diary_book_ids': []
        }
    ],
    '26': [
        {
            'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_import_ids': ['131', '1311', '1312', '221', '222', '2281'],
            'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
        }
    ],

    '27': [
        {
            'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129'],
            'reciprocal_account_import_ids': ['515', '5151', '5152', '5153', '5154', '5155', '5158'],
            'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
        }
    ],
    '31': [
        {
            'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_import_ids': ['41111', '41112', '4112', '4113', '4118'],
            'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
        }
    ],
    '32': [
        {
            'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
            'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_export_ids': ['41111', '41112', '4112', '4113', '4118', '419', '4191', '4192'],
            'diary_book_ids': []
        }
    ],
    '33': [
        {
            'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_import_ids': ['171', '3411', '34111', '34112', '3431', '34311', '34312', '34313',
                                              '3432', '41112'],
            'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
        }
    ],
    '34': [
        {
            'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
            'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129'],
            'reciprocal_account_export_ids': ['171', '3411', '34111', '34112', '3431', '34311', '34312', '34313',
                                              '3432', '41112'],
            'diary_book_ids': []
        }
    ],
    '35': [
        {
            'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
            'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_export_ids': ['3412'],
            'diary_book_ids': []
        }
    ],
    '36': [
        {
            'account_number_import_ids': [], 'reciprocal_account_import_ids': [],
            'account_number_export_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132'],
            'reciprocal_account_export_ids': ['3381', '3382', '3383', '3384', '3385', '3386', '3387', '3388', '33881',
                                              '33882', '33883', '33884', '33885', '4211', '4212'],
            'diary_book_ids': []
        }
    ],
    '60': [
        {
            'account_number_import_ids': ['110'],
            'reciprocal_account_import_ids': [], 'account_number_export_ids': [], 'reciprocal_account_export_ids': [],
            'diary_book_ids': [],
            'target_id': 112
        }
    ],
    '61': [
        {
            'account_number_import_ids': ['111', '1111', '11110', '1112', '11120', '1113', '1114', '1115', '112',
                                          '1121', '11210', '11211', '11212', '11213', '11214', '11215', '11216',
                                          '11218', '11219', '1122', '11221', '11221 TGNH USD - NH ACB', '11222',
                                          '11223', '11224', '11226', '11227', '11229', '1123', '11230', '11231',
                                          '11232', '11233', '11235', '11236', '11237', '11238', '1124', '1125', '1126',
                                          '1127', '1128', '1129', '113', '1131', '1132', '128', '1281', '1282', '1283',
                                          '1288'],
            'reciprocal_account_import_ids': ['4131'],
            'account_number_export_ids': [], 'reciprocal_account_export_ids': [], 'diary_book_ids': []
        }
    ],
}

DATA_CATEG_CASHFLOW = {'30': {'total_categ_ids': ['21', '22', '23', '24', '25', '26', '27']},
                       '40': {'total_categ_ids': ['31', '32', '33', '34', '35', '36']},
                       '70': {'total_categ_ids': ['50', '60', '61']}, '50': {'total_categ_ids': ['20', '30', '40']},
                       '20': {'total_categ_ids': ['01', '02', '03', '04', '05', '06', '07']}}

class CashFlows(models.Model):
    _name = 'cash.flows'
    _description = 'Cash Flow'
    _rec_name = 'categ_name'
    _order = "stt_calculate"

    report_type = fields.Selection([
        ('statements_cash_flows', 'Statements of cash flows')
    ], string="Report Type", default='statements_cash_flows')
    categ_name = fields.Char('Category name')
    code = fields.Char('Code')
    parent_level = fields.Many2one('cash.flows')
    apply_by = fields.Selection([
        ('total_categ', 'Total Category'),
        ('accounting_balance_sheet', 'Accounting balance sheet'),
        ('according_method_of_create', 'According Method Of Create')
    ], string="Apply by")
    stt_calculate = fields.Integer('STT')
    account_ids = fields.Many2many('account.account', string="Account systems")
    total_categ_ids = fields.Many2many('cash.flows','rel_cash_total_categ', 'balance_id', 'total_categ_id', string="Total Categorys")
    active = fields.Boolean(string="Active", default=True)
    line_ids = fields.One2many('cash.flows.line', 'method_of_create_id')

    in_business_cycle = fields.Boolean('In the business cycle')
    company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)
    is_bold_report = fields.Boolean('Bold in report')
    is_italic_report = fields.Boolean('Italic in report')
    target_id = fields.Many2one('accounting.balance.sheet','Targets')
    column = fields.Selection([
        ('number_first_year', 'Beginning Balance'),
        ('number_last_year', 'Ending Balance')
    ])

    def create_missing_cash_flow_field_ids(self):
        if not self._context.get("create_company"):
            for record in self:
                check_exists = self.search([('code', '=', record.code)])
                record_exists = check_exists - record
                try:
                    if record_exists and len(record_exists) == 1:
                        record.update({'active': False})
                    elif record_exists and len(record_exists) > 1:
                        pass
                    else:
                        data = SAMPLE_CASHFLOW_DATA.get(record.code, False)
                        record.line_ids = [(5, 0, 0)]
                        if data:
                            for da in data:
                                account_number_import_ids = self.env['account.account'].search(
                                    [('code', 'in', da.get('account_number_import_ids', []))]).ids
                                reciprocal_account_import_ids = self.env['account.account'].search(
                                    [('code', 'in', da.get('reciprocal_account_import_ids', []))]).ids
                                account_number_export_ids = self.env['account.account'].search(
                                    [('code', 'in', da.get('account_number_export_ids', []))]).ids
                                reciprocal_account_export_ids = self.env['account.account'].search(
                                    [('code', 'in', da.get('reciprocal_account_export_ids', []))]).ids
                                diary_book_ids = self.env['account.account'].search(
                                    [('code', 'in', da.get('diary_book_ids', []))]).ids
                                target_id = self.env['accounting.balance.sheet'].search([('code', '=', da.get('target_id', False)),('company_id','=',record.company_id.id)],limit=1).id

                                if target_id:
                                    record.target_id = target_id
                                record.line_ids.create({
                                    'method_of_create_id': record.id,
                                    'account_number_import_ids': [(6, 0, account_number_import_ids)],
                                    'reciprocal_account_import_ids': [(6, 0, reciprocal_account_import_ids)],
                                    'account_number_export_ids': [(6, 0, account_number_export_ids)],
                                    'reciprocal_account_export_ids': [(6, 0, reciprocal_account_export_ids)],
                                    'diary_book_ids': [(6, 0, diary_book_ids)],
                                })
                except IndexError:
                    pass
        self.action_duplicate_accounts_cashflow_company()

    def action_duplicate_accounts_cashflow_company(self):
        self = self.sudo()
        copy_records = self.env["cash.flows"]
        if not self._context.get("new_company"):
            companies = self.env["res.company"].search([("id", "!=", self.env.company.id)])
        else:
            company_id = self.env["res.company"].search([("id", "!=", self._context.get("new_company"))],limit=1,order="create_date asc")
            search_self = self.search([('company_id','=',company_id.id)]) if company_id else False
            for se in search_self:
                copy_records += se.sudo().copy({"company_id": self._context.get("new_company"),
                                                    "total_categ_ids": [(6, 0, [])],
                                                    "line_ids": [(5, 0, 0)]
                                                    })
        for record in self:
            for company in companies:
                copy_records += record.sudo().copy({"company_id": company.id,
                                                    "total_categ_ids": [(6, 0, [])],
                                                    "line_ids": [(5, 0, 0)]
                                                    })
        for record in copy_records:
            data = DATA_CATEG_CASHFLOW.get(record.code, False)
            data_flows = SAMPLE_CASHFLOW_DATA.get(record.code, False)
            if data:
                total_categ_ids = copy_records.filtered_domain([("code", "in", data.get("total_categ_ids"))])
                record.sudo().update({"total_categ_ids": [(6, 0, total_categ_ids.ids)]})
            if data_flows:
                for da in data_flows:
                    account_number_import_ids = self.env['account.account'].search(
                        [('code', 'in', da.get('account_number_import_ids', []))]).ids
                    reciprocal_account_import_ids = self.env['account.account'].search(
                        [('code', 'in', da.get('reciprocal_account_import_ids', []))]).ids
                    account_number_export_ids = self.env['account.account'].search(
                        [('code', 'in', da.get('account_number_export_ids', []))]).ids
                    reciprocal_account_export_ids = self.env['account.account'].search(
                        [('code', 'in', da.get('reciprocal_account_export_ids', []))]).ids
                    diary_book_ids = self.env['account.account'].search(
                        [('code', 'in', da.get('diary_book_ids', []))]).ids

                    record.sudo().line_ids.create({
                        'method_of_create_id': record.id,
                        'account_number_import_ids': [(6, 0, account_number_import_ids)],
                        'reciprocal_account_import_ids': [(6, 0, reciprocal_account_import_ids)],
                        'account_number_export_ids': [(6, 0, account_number_export_ids)],
                        'reciprocal_account_export_ids': [(6, 0, reciprocal_account_export_ids)],
                        'diary_book_ids': [(6, 0, diary_book_ids)],
                    })



class CashFlowLine(models.Model):
    _name = 'cash.flows.line'

    method_of_create_id = fields.Many2one('cash.flows')
    account_number_import_ids = fields.Many2many('account.account')
    reciprocal_account_import = fields.Many2many('account.account', 'import_account')
    reciprocal_account_import_ids = fields.Many2many('account.account', 'reciprocal_account_import_ref',
                                                     'cash_flows_import_id', 'account_account_import_id')
    account_number_export_ids = fields.Many2many('account.account', 'account_number_export_ref',
                                                 'cash_flows_export_id', 'account_account_export_id')
    reciprocal_account_export_ids = fields.Many2many('account.account', 'eciprocal_account_export_ref',
                                                     'cash_flows_export_ids',
                                                     'account_account_export_ids')
    diary_book_ids = fields.Many2many('account.journal')
