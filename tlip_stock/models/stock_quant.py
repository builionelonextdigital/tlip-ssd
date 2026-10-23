from odoo import api, models, fields, _
from odoo.exceptions import UserError


class QuantPackage(models.Model):
    _inherit = "stock.quant.package"

    usage = fields.Char()
    stock_serial_ids = fields.One2many("tlip.stock.serial", "package_id")
    package_type_id = fields.Many2one(string="Asset Code Type")
    asset_ids = fields.One2many(
        'account.asset', 'package_id', string='Related Depreciations'
    )

    @api.constrains("name", "company_id")
    def _check_unique_name(self):
        for record in self:
            if not record.name:
                continue
            duplicate_package_counts = record.search_count(
                [
                    ("id", "!=", record.id),
                    ("name", "=", record.name),
                    ("company_id", "=?", record.company_id.id),
                ]
            )
            if duplicate_package_counts > 0:
                raise UserError(
                    _(f"Asset Code Name '{record.name}' already existed. Please select another name."))


class StockQuant(models.Model):
    _inherit = "stock.quant"

    package_id = fields.Many2one(
        'stock.quant.package',
        'Asset Code'
    )


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    name = fields.Char(string="Asset Code Type")
