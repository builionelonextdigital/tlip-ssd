from odoo import api, fields, models, _


class AnalyticReport(models.Model):
    _name = 'analytic.report'
    _description = 'Analytic Report'

    name = fields.Char(string='Analytic Report', required=True)
    line_ids = fields.One2many(
        'analytic.report.line', 'analytic_report_id', 'Lines')


class AnalyticReportLine(models.Model):
    _name = 'analytic.report.line'
    _description = 'Analytic Report Line'

    analytic_report_id = fields.Many2one('analytic.report', required=True)
    account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Budget Code',
        ondelete='restrict', required=True
    )
    budget_main_categ_id = fields.Many2one(
        'budget.category',
        related='account_id.budget_main_categ_id', store=True,
        string='Budget Main Category'
    )
    budget_2nd_categ_id = fields.Many2one(
        'budget.category',
        related='account_id.budget_2nd_categ_id', store=True,
        string='Budget Secondary Category'
    )
    budget_detailed_categ_id = fields.Many2one(
        'budget.category',
        related='account_id.budget_category_id', store=True,
        string='Budget Detailed Category'
    )
