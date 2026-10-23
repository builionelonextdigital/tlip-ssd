from odoo import fields, models, api


class CashFlowTemplate(models.Model):
    _name = 'cash.flows.template'

    name = fields.Char('Name')
    template_type = fields.Selection(selection=[('statements_cash_flows', 'Statements of cash flows')],
                                     string="Template Type", default='statements_cash_flows')
    # Old
    line_ids = fields.One2many('cash.flows.template.line', 'template_id')
    # New
    cash_flows_ids = fields.Many2many(comodel_name='cash.flows',
                                   relation='cash_flows_template_rel', column1='template_id',
                                   column2='sheet_id', domain="[('report_type', '=', template_type)]")
    company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)


class CashFlowsTemplateLine(models.Model):
    _name = 'cash.flows.template.line'


    template_id = fields.Many2one('cash.flows.template')
    domain_balance = fields.Selection(related="template_id.template_type")
    balance_id = fields.Many2one('cash.flows', 'Assets', required=True, domain="[('report_type', '=', domain_balance)]")
    code = fields.Char('Code')

    @api.onchange('balance_id')
    def onchange_balance_id(self):
        if self.balance_id:
            self.code = self.balance_id.code
