from odoo import api, fields, models, _


class LandPlotMergeLine(models.Model):
    _name = 'stock.location.merge.line'
    _description = 'Land Plot Merge Line'

    cr_id = fields.Many2one(
        comodel_name="stock.location.cr",
        required=True,
        ondelete="cascade"
    )
    plot_view_id = fields.Many2one(related='cr_id.plot_view_id')
    land_plot_id = fields.Many2one(
        comodel_name='stock.location',
        required=True,
        context={'short_name': True},
        domain="[('id', 'in', available_land_plot_ids)]"
    )
    gross_area = fields.Float(related='land_plot_id.gross_area')
    saleable_area = fields.Float(related='land_plot_id.saleable_area')
    lease_state = fields.Selection(related='land_plot_id.lease_state')
    current_contract_id = fields.Many2one(
        comodel_name='leasing.agreement',
        compute='_compute_land_plot'
    )
    contract_period_str = fields.Char(compute="_compute_land_plot", string="Contract Period")
    available_land_plot_ids = fields.Many2many('stock.location', compute="_compute_available_land_plot_ids")

    @api.depends('land_plot_id')
    def _compute_land_plot(self):
        date_format = self.env['res.lang']._lang_get(self.env.user.lang).date_format

        for record in self:
            current_contract = record.land_plot_id.current_contract_id
            start = current_contract.commence_date \
                and current_contract.commence_date.strftime(date_format) or ''
            end = current_contract.expiry_date \
                and current_contract.expiry_date.strftime(date_format) or ''

            record.current_contract_id = current_contract
            record.contract_period_str = f'{start} - {end}'

    @api.depends('cr_id', 'plot_view_id')
    def _compute_available_land_plot_ids(self):
        land_plots = self.env["stock.location"].search([
            ('is_land_plot', '=', True),
            ('is_plot_view', '=', False),
            ('state', '=', 'confirm'),
            ('merge_split_remark', '=', False)
        ])
        for record in self:
            available_land_plots = []
            if record.plot_view_id:
                existing_land_plots = record.cr_id.merge_land_plot_ids.land_plot_id
                available_land_plots = (land_plots - existing_land_plots).filtered(
                    lambda land, location_id=record.plot_view_id: land.location_id.id == location_id.id
                )
            record.available_land_plot_ids = available_land_plots
