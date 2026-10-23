from odoo import models, fields, api, _
from odoo.addons.account.models.product import ACCOUNT_DOMAIN

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    invoice_description_vn = fields.Char('Invoice Description (VN)')
    invoice_description_en = fields.Char('Invoice Description (EN)')
    income_budget_code_id = fields.Many2one('budget.code', string='Income Budget Code')
    expense_budget_code_id = fields.Many2one('budget.code', string='Expense Budget Code')
    
    property_deferred_account_income_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Deferred Income Account",
        domain=ACCOUNT_DOMAIN,
        tracking=True,
        ondelete='restrict',
    )
    property_deferred_account_expense_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Deferred Expense Account",
        domain=ACCOUNT_DOMAIN,
        tracking=True,
        ondelete='restrict',
    )

    epe_taxes_id = fields.Many2many('account.tax', 'epe_product_taxes_rel', 'prod_id', 'tax_id',
        string="Sales Taxes (EPE)",
        help="Default taxes used when selling the product for EPE Customer",
        domain=[('type_tax_use', '=', 'sale')],
        default=lambda self: self.env.companies.account_sale_tax_id or self.env.companies.root_id.sudo().account_sale_tax_id,
    )

    def _get_tax(self, company, tax_apply_type='non_epe'):
        taxes = self.with_company(company).taxes_id
        if tax_apply_type != 'non_epe':
            taxes = self.with_company(company).epe_taxes_id
        return taxes.filtered(lambda r: r.company_id == company)[:1]
