from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAssetGroup(models.Model):
    _inherit = 'account.asset.group'

    asset_prefix = fields.Char(string='Asset Prefix', tracking=True, copy=False)
    asset_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Asset Sequence',
        copy=False,
        readonly=True,
        ondelete='set null',
    )

    @api.constrains('asset_prefix', 'company_id')
    def _check_unique_prefix_per_company(self):
        for rec in self:
            if not rec.asset_prefix:
                continue
            duplicate = self.search([
                ('asset_prefix', '=', rec.asset_prefix),
                ('company_id', '=', rec.company_id.id),
                ('id', '!=', rec.id),
            ], limit=1)
            if duplicate:
                raise UserError(
                    _("Asset prefix '%s' is already used by another group in company '%s'.")
                    % (rec.asset_prefix, rec.company_id.name)
                )

    def _create_asset_sequence(self):
        self.ensure_one()
        # Do not need to update prefix in sequence, the asset_prefix may change but the sequence should dynamically, no need to follow the changes
        seq = self.env['ir.sequence'].create({
            'name': _('Asset Code Sequence - %s (%s)') % (self.asset_prefix, self.company_id.name),
            'padding': 4,
            'prefix': '%(y)s',
            'use_date_range': True,
            'number_next': 1,
            'number_increment': 1,
            'company_id': self.company_id.id,
        })
        self.asset_sequence_id = seq
        return seq

    def _get_or_create_sequence(self):
        self.ensure_one()
        if not self.asset_prefix:
            return False
        if not self.asset_sequence_id:
            return self._create_asset_sequence()
        return self.asset_sequence_id

    def write(self, vals):
        res = super().write(vals)
        if 'asset_prefix' in vals:
            for rec in self:
                if rec.asset_prefix and rec.asset_sequence_id:
                    rec.asset_sequence_id.write({'name': _('Asset Code Sequence - %s (%s)') % (rec.asset_prefix, rec.company_id.name)})
        return res
