from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


CR_TYPE_VALIDATE_FUNCTION_MAPPING = {
    "merge": "_validate_merge_land_plot",
    "split": "_validate_split_land_plot",
}

CR_TYPE_FUNC_CONFIRM_MAPPING = {
    "merge": "_action_merge_land_plot",
    "split": "_action_split_land_plot",
}


class LandPlotCR(models.Model):
    _name = 'stock.location.cr'
    _inherit = ["mail.thread", "mail.activity.mixin", "approval.matrix.mixin"]
    _description = "Change Land Plot"

    def _domain_plot_view(self):
        return [
            ('is_plot_view', '=', True),
            ('state', '=', 'confirm')
        ]

    name = fields.Char(
        string="Request", required=True, default="New", copy=False,
        index='trigram', tracking=True
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("wait_for_approval", "Waiting for Approval"),
            ("approved", "Approved"),
            ("confirm", "Completed"),
            ("rejected", "Rejected"),
            ('cancel', 'Cancelled')
        ], string="Status", default="draft",
        tracking=True, copy=False
    )
    plot_view_id = fields.Many2one(
        comodel_name="stock.location",
        tracking=True,
        domain=_domain_plot_view
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Requester",
        check_company=True, tracking=True
    )
    cr_type = fields.Selection(
        selection=[
            ('merge', 'Merge'),
            ('split', 'Split'),
            ('update', 'Update')
        ], required=True, default="merge",
        string="Change Type", tracking=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company.id,
        required=True, index=True,
        ondelete="cascade"
    )
    effective_date = fields.Date(default=fields.Date.today, copy=False, required=True)
    description = fields.Text()
    land_plot_id = fields.Many2one(
        comodel_name='stock.location',
        context={'short_name': True},
        domain="[('is_land_plot', '=', True), ('is_plot_view', '=', False), ('merge_split_remark', '=', False), ('location_id', '=', plot_view_id)]"
    )
    original_gross_area = fields.Float(related='land_plot_id.gross_area')
    original_saleable_area = fields.Float(related='land_plot_id.saleable_area')
    original_lease_state = fields.Selection(related='land_plot_id.lease_state')
    land_plot_contract_id = fields.Many2one(
        comodel_name='leasing.agreement',
        compute='_compute_land_plot'
    )
    land_plot_contract_period_str = fields.Char(compute="_compute_land_plot", string="Contract Period")

    new_name = fields.Char(string="Destination Land Plot")
    new_date_start = fields.Date(string="Date Start", compute="_compute_land_plot_data", store=True, readonly=False)
    new_date_end = fields.Date(string="Date End", compute="_compute_land_plot_data", store=True, readonly=False)
    new_gross_area = fields.Float(string="Gross Area", compute="_compute_land_plot_data", store=True, readonly=False)
    new_saleable_area = fields.Float(string="Saleable Area", compute="_compute_land_plot_data", store=True, readonly=False)
    new_land_plot_category_id = fields.Many2one(
        string="Category",
        comodel_name='land.plot.category',
        compute="_compute_land_plot_data",
        store=True, readonly=False
    )
    merge_land_plot_ids = fields.One2many(
        comodel_name='stock.location.merge.line',
        inverse_name="cr_id"
    )
    split_land_plot_ids = fields.One2many(
        comodel_name='stock.location.split.line',
        inverse_name="cr_id"
    )
    number_to_split = fields.Integer()

    @api.constrains("new_date_start", "new_date_end")
    def _check_dates(self):
        # Note: update condition in create function
        if any(record.new_date_start > record.new_date_end for record in self if record.new_date_start and record.new_date_end):
            raise ValidationError(_("Start date should precede the end date."))

    @api.constrains("new_gross_area", "new_saleable_area")
    def _check_new_area(self):
        # Note: update condition in create function
        if any(record.new_gross_area < record.new_saleable_area for record in self):
            raise ValidationError(_("Saleable area should not be larger than gross area"))

    @api.depends("land_plot_id", "merge_land_plot_ids.land_plot_id", "cr_type")
    def _compute_land_plot_data(self):
        for rec in self:
            vals = rec._prepare_compute_split_merge_type_vals()
            rec.update(vals)

    @api.depends('land_plot_id')
    def _compute_land_plot(self):
        date_format = self.env['res.lang']._lang_get(self.env.user.lang).date_format

        for record in self:
            current_contract = record.land_plot_id.current_contract_id
            start = current_contract.commence_date \
                and current_contract.commence_date.strftime(date_format) or ''
            end = current_contract.expiry_date \
                and current_contract.expiry_date.strftime(date_format) or ''

            record.land_plot_contract_id = current_contract
            record.land_plot_contract_period_str = f'{start} - {end}'

    @api.onchange('plot_view_id')
    def _onchange_plot_view_id(self):
        self.update({
            "land_plot_id": False,
        })

    @api.onchange('number_to_split', 'land_plot_id')
    def onchange_number_to_split(self):
        if self.number_to_split and self.number_to_split > 1:
            child_shop_vals = [(5, 0, 0)]
            land_plot = self.land_plot_id
            parent_shop_name = land_plot.name
            new_date_start = land_plot.get_period_date_start_new_land_plots(added_days=1)
            for i in range(65, 65 + self.number_to_split):
                # Naming rule for child shops is parent_shop_name-A, parent_shop_name-B, ...We loop from 65 since we have chr(65) = 'A'.
                child_shop_name = f"{parent_shop_name}-{chr(i)}"
                
                child_shop_vals.append((0, 0, {
                    'name': child_shop_name,
                    'gross_area': float(land_plot.gross_area / self.number_to_split),
                    'saleable_area': float(land_plot.saleable_area / self.number_to_split),
                    'land_plot_category_id': land_plot.land_plot_category_id.id,
                    'date_start': new_date_start,
                    'date_end': new_date_start,
                }))
            self.update({'split_land_plot_ids':  child_shop_vals})

        if not self.number_to_split or not self.land_plot_id:
            self.update({'split_land_plot_ids': None})

    def action_submit_approval(self):
        self._validate_submit_approval()
        action = super().action_submit_approval()
        action['context']['default_name'] = _(f'Approval Change Land Plot {self.name}')
        return action

    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })

    def action_reset(self):
        self.write({
            'state': 'draft',
        })

    def action_complete(self):
        self._trigger_action_complete()

    def _get_location_action_form(self, land_plots):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "tlip_stock.action_land_plot_view")

        if len(land_plots) == 1:
            action['views'] = [(self.env.ref('tlip_stock.land_plot_view_form').id, 'form')]
            action['res_id'] = land_plots.id
            action['view_mode'] = 'form'

        else:
            action['domain'] = [('id', 'in', land_plots.ids)]
        return action

    def _prepare_compute_split_merge_type_vals(self):
        land_plots = self.env["stock.location"]
        vals = {}
        if self.cr_type == "merge":
            land_plots |= self.merge_land_plot_ids.land_plot_id
        else:
            land_plots |= self.land_plot_id

        categories = land_plots.land_plot_category_id
        new_date_start = land_plots.get_period_date_start_new_land_plots(added_days=1)
        vals.update({
            "new_saleable_area": sum(land_plots.mapped("saleable_area")),
            "new_gross_area": sum(land_plots.mapped("gross_area")),
            "new_date_start": new_date_start,
            "new_date_end": new_date_start,
            "new_land_plot_category_id": categories and categories[0]
        })

        return vals

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval',
        })
        return result

    def _trigger_action_approve(self):
        self.write({'state': 'approved'})
        self._send_email_notify_complete()

    def _trigger_action_refuse(self):
        self.write({'state': 'rejected'})

    def _trigger_action_complete(self):
        self._validate_complete_approval()
        for rec in self:
            method = CR_TYPE_FUNC_CONFIRM_MAPPING.get(rec.cr_type)
            if method:
                land_plot_action = getattr(rec, method)()

        self.write({'state': 'confirm'})
        return land_plot_action

    def _trigger_action_withdraw(self, reason: str):
        self.action_cancel()
        super()._trigger_action_withdraw(reason)

    def _validate_submit_approval(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(
                    _('You cannot submit a change land plot that is not in Draft state.'))

            # TODO: Remove and add function for update
            if record.cr_type == "update":
                raise UserError(_("Not Implement"))

            validate_method = CR_TYPE_VALIDATE_FUNCTION_MAPPING.get(record.cr_type)
            if validate_method:
                getattr(record, validate_method)()

    def _validate_complete_approval(self):
        for record in self:
            if record.state != 'approved':
                raise UserError(
                    _('You cannot complete a change land plot that is not in Approved state.'))

            validate_method = CR_TYPE_VALIDATE_FUNCTION_MAPPING.get(record.cr_type)
            if validate_method:
                getattr(record, validate_method)()

    def _validate_merge_land_plot(self):
        self.ensure_one()
        merge_lines = self.merge_land_plot_ids
        land_plots = self.merge_land_plot_ids.land_plot_id
        if len(merge_lines) < 2:
            raise UserError(_('Minimum merge should select two land plots'))

        if len(merge_lines) != len(land_plots):
            raise UserError(_('Found duplicate land plots in merge lines.'))

        if land_plots.location_id.ids != self.plot_view_id.ids:
            plot_view = self.plot_view_id.with_context({"short_name": True})
            invalid_land_plots = land_plots.filtered_domain(
                [('location_id', '!=', plot_view.id)]
            ).with_context({"short_name": True})
            raise UserError(
                _(f"Land Plot(s) {', '.join(invalid_land_plots.mapped('name'))} does not belong to Plot View {plot_view.name}"))

        if any(land_plots.mapped('merge_split_remark')):
            invalid_land_plots = land_plots.filtered_domain(
                [('merge_split_remark', '!=', False)]
            ).with_context({"short_name": True})

            raise UserError(
                _(f"Operations cannot be performed on merged or split location(s): {', '.join(invalid_land_plots.mapped('name'))}"))

        threshold_date_start = land_plots.get_period_date_start_new_land_plots()
        if threshold_date_start and self.new_date_start < threshold_date_start:
            date_format = self.env['res.lang']._lang_get(self.env.user.lang).date_format
            raise UserError(
                _(f"New start date should be after {threshold_date_start.strftime(date_format)}, please check again."))

        if self.new_gross_area > sum(merge_lines.mapped("gross_area")):
            raise UserError(_("Gross area should not be larger than total gross area"))

        if self.new_saleable_area < sum(merge_lines.mapped("saleable_area")):
            raise UserError(_("Saleable area should not be smaller than total saleable area"))

    def _validate_split_land_plot(self):
        self.ensure_one()
        split_lines = self.split_land_plot_ids
        land_plot = self.land_plot_id.with_context({"short_name": True})
        if land_plot.merge_split_remark:
            raise UserError(
                _(f"Operations cannot be performed on merged or split parent location: {land_plot.name}"))

        if self.number_to_split <= 1:
            raise ValidationError(_(
                'Cannot not split the land plot into less than 2 child land plots'))

        if len(split_lines) != len(set(split_lines.mapped("name"))):
            raise ValidationError(_("Found duplicate new land plot name"))

        threshold_date_start = land_plot.get_period_date_start_new_land_plots()
        split_line_date_start = min(split_lines.mapped("date_start"))
        if threshold_date_start and split_line_date_start < threshold_date_start:
            date_format = self.env['res.lang']._lang_get(self.env.user.lang).date_format
            raise UserError(
                _(f"Split shop minimum start date should be after {threshold_date_start.strftime(date_format)}, please check again."))

        if sum(split_lines.mapped("gross_area")) > land_plot.gross_area:
            raise UserError(_("Sum of gross area of child should not be larger than parent gross area"))

        if sum(split_lines.mapped("saleable_area")) < land_plot.saleable_area:
            raise UserError(_("Sum of gross saleable of child should not be smaller than parent saleable area"))

    def _action_merge_land_plot(self):
        self.ensure_one()

        land_plot_vals = self._prepare_new_info_land_plot({
            'is_land_plot': True,
            'is_plot_view': False,
            }
        )

        land_plot = self.env['stock.location'].create(land_plot_vals)
        land_plot.action_confirm()
        self.merge_land_plot_ids.land_plot_id.action_set_merge_state(child_id=land_plot, merged_date_start=self.new_date_start)

        action = self._get_location_action_form(land_plots=land_plot)

        return action

    def _action_split_land_plot(self):
        self.ensure_one()
        default_vals = {
            'is_land_plot': True,
            'is_plot_view': False,
            'location_id': self.plot_view_id.id,
        }
        land_plot_vals = []
        for split_line in self.split_land_plot_ids:
            vals = split_line._prepare_new_info_land_plot(default_vals)
            land_plot_vals.append(vals)

        land_plots = self.env['stock.location'].create(land_plot_vals)
        land_plots.action_confirm()
        self.land_plot_id.action_set_split_state(child_ids=land_plots, split_date_start=min(self.split_land_plot_ids.mapped("date_start")))

        action = self._get_location_action_form(land_plots=land_plots)

        return action

    def _prepare_new_info_land_plot(self, vals={}):
        self.ensure_one()
        land_plot_vals = {
            'name': self.new_name,
            'location_id': self.plot_view_id.id,
            'date_start': self.new_date_start,
            'date_end': self.new_date_end,
            'gross_area': self.new_gross_area,
            'saleable_area': self.new_saleable_area,
            'land_plot_category_id' :self.new_land_plot_category_id.id
        }
        if vals:
            land_plot_vals.update(vals)
        return land_plot_vals

    def _send_email_notify_complete(self):
        template = self.env.ref('tlip_leasing.stock_location_cr_mail_template')
        if template:
            for rec in self:
                template.send_mail(rec.id, force_send=False, email_values={
                    'email_to': rec.user_id.email,
                })

    @api.model_create_multi
    def create(self, vals_list):
        StockLocationSplitLine = self.env['stock.location.split.line']
        for vals in vals_list:
            # Check condition before constrains is called, to avoid sequence increment before error
            if 'new_date_start' in vals and 'new_date_end' in vals and vals['new_date_start'] > vals['new_date_end']:
                raise ValidationError(_("Start date should precede the end date."))

            if vals['new_gross_area'] and vals['new_saleable_area'] and vals['new_gross_area'] < vals['new_saleable_area']:
                raise ValidationError(_("Saleable area should not be larger than gross area"))

            if 'split_land_plot_ids' in vals:
                StockLocationSplitLine.check_constrains_upon_create(vals['split_land_plot_ids'])

            if 'name' not in vals or vals['name'] == _("New"):
                vals['name'] = self.env['ir.sequence'].next_by_code('change.land.plot')
        records = super().create(vals_list)
        return records
