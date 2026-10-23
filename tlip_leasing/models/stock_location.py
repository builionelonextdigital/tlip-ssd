from odoo import models, fields, api, _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class LandPlot(models.Model):
    _inherit = 'stock.location'

    leasing_quotation_ids = fields.One2many('leasing.quotation', 'land_plot_id')
    agreement_ids = fields.One2many('leasing.agreement', 'land_plot_id', string='Agreements')
    current_quotation_id = fields.Many2one('leasing.quotation', compute='_compute_current_quotation')
    current_reservation_id = fields.Many2one('leasing.agreement', compute='_compute_current_reservation')
    current_contract_id = fields.Many2one('leasing.agreement', compute='_compute_current_contract')
    current_tenant_id = fields.Many2one('res.partner', compute='_compute_current_tenant')
    current_tenant_count = fields.Integer(compute='_compute_current_tenant')
    current_lessee_id = fields.Many2one('res.partner', compute='_compute_current_lessee')
    lease_period = fields.Char(compute='_compute_lease_period')
    registered_power_capacity = fields.Float('Registered Power Capability', readonly=True)
    registered_water_consumption = fields.Float('Registered Water Consumption', readonly=True)
    registered_sprinkler_rent = fields.Float('Registered Sprinkler System Rent', readonly=True)
    leasing_history_ids = fields.One2many('leasing.history', 'land_plot_id', string='Leasing History')
    merge_split_remark = fields.Selection(
        selection=[
            ('merge', 'Merge'),
            ('split', 'Split'),
        ], copy=False
    )
    merge_split_parent_ids = fields.Many2many('stock.location', relation="parent_location_rel",
                                              column1="location_id", column2="parent_id", copy=False)
    merge_split_child_ids = fields.Many2many('stock.location', relation="child_location_rel", context={'active_test': False},
                                             column1="location_id", column2="child_id", copy=False)

    def _compute_current_quotation(self):
        today = fields.Date.today()
        for record in self:
            record.current_quotation_id = record.leasing_quotation_ids.filtered_domain([
                ('state', '=', 'confirm'),
                ('issued_date', '<=', today),
                ('due_date', '>=', today)
            ])[:1]

    def _compute_current_reservation(self):
        today = fields.Date.today()
        for record in self:
            record.current_reservation_id = record.agreement_ids.filtered_domain([
                ('state', '=', 'approve'),
                ('agreement_type', '=', 'reservation'),
                ('issued_date', '<=', today),
                ('expiry_date', '>=', today)
            ])[:1]

    def _compute_current_contract(self):
        today = fields.Date.today()
        for record in self:
            record.current_contract_id = record.agreement_ids.filtered_domain([
                ('state', '=', 'approve'),
                ('agreement_type', '=', 'contract'),
                ('issued_date', '<=', today),
                ('expiry_date', '>=', today)
            ])[:1]

    def _compute_current_tenant(self):
        for record in self:
            current_agreement = record.current_contract_id or record.current_reservation_id
            current_tenant = current_agreement.lessee_id
            record.current_tenant_id = current_tenant
            record.current_tenant_count = len(current_tenant)

    def _compute_current_lessee(self):
        for record in self:
            record.current_lessee_id = record.current_contract_id.lessee_id

    def _compute_lease_period(self):
        for record in self:
            if record.current_contract_id:
                period_from = record.current_contract_id.issued_date.strftime('%d/%m/%Y')
                period_to = record.current_contract_id.expiry_date.strftime('%d/%m/%Y')
                record.lease_period = f"{period_from} - {period_to}"
            else:
                record.lease_period = False
    def get_period_date_start_new_land_plots(self, added_days=0):
        date_start_lst = []
        for land in self:
            active_leases = land.current_contract_id | land.current_reservation_id
            expiry_date_lst = [expiry_date for expiry_date in active_leases.mapped('expiry_date') if expiry_date]
            if expiry_date_lst:
                date_start_lst.append((max(expiry_date_lst)))
            elif land.date_start:
                date_start_lst.append(land.date_start)

        return (max(date_start_lst) + timedelta(days=added_days)) if date_start_lst else False

    def action_set_merge_state(self, child_id, merged_date_start=None):
        vals = {
            'merge_split_remark': 'merge',
            'merge_split_child_ids': [(6, 0, child_id.ids)],
        }
        if merged_date_start:
            vals.update({
                'date_end': merged_date_start + relativedelta(days=-1)
            })

        self.write(vals)
        child_id.write({'merge_split_parent_ids': [(6, 0, self.ids)]})
        child_id.message_post(body=_(f"{child_id.name} is merged from locations: {', '.join(self.mapped('name'))}"))

    def action_set_split_state(self, child_ids, split_date_start=None):
        vals = {
            'merge_split_remark': 'merge',
            'merge_split_child_ids': [(6, 0, child_ids.ids)],
        }
        if split_date_start:
            vals.update({
                'date_end': split_date_start + relativedelta(days=-1)
            })

        self.write(vals)
        child_ids.write({'merge_split_parent_ids': [(6, 0, self.ids)]})
        for child in child_ids:
            child.message_post(body=_(f"{child.name} is splitted from location: {self.name}"))

    def _current_lease_quotations(self):
        self.ensure_one()
        today = fields.Date.today()
        return self.leasing_quotation_ids.filtered_domain([
            ('state', '=', 'confirm'),
            ('due_date', '>=', today)
        ])

    def _get_current_lease_quotations(self):
        self.ensure_one()
        today = fields.Date.today()
        return self.leasing_quotation_ids.filtered_domain([
            ('state', '!=', 'cancel'),
            ('issued_date', '<=', today),
            ('due_date', '>=', today)
        ])
    
    def _get_location_lease_state(self):
        self.ensure_one()
        current_quotations = self._get_current_lease_quotations()
        lease_state = 'vacant'
        if self.current_contract_id:
            lease_state = 'occupied'
        elif self.current_reservation_id:
            lease_state = 'reserved'
        elif current_quotations:
            lease_state = 'under_negotiation'
        return lease_state

    def action_view_land_plot_detail(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('tlip_leasing.action_land_plot_detail')
        action.update({
            'target': 'current',
            'domain':  [
                ('location_id', '=', self.id),
                ('is_land_plot', '=', True),
            ]
        })
        return action

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)

        if view_type == 'form':
            hidden_btns = arch.xpath("//button")
            for node in hidden_btns:
                # Add condition if not active to all buttons in form view
                archived_condition = "not active"
                if node.get("invisible"):
                    node.set('invisible', f"{archived_condition} or ({node.attrib.pop('invisible')})")
                else:
                    node.set('invisible', archived_condition)
        return arch, view

    @api.model
    def cron_update_location_lease_state(self):
        for location in self.sudo().search([]):
            location.lease_state = location._get_location_lease_state()

    def write(self, vals):
        if any(not rec.active for rec in self if rec.is_land_plot) and not (self.env.su or self.env.context.get("allow_update_archived")):
            raise UserError(_("Do not allow to update on archived Land Plot"))
        return super().write(vals)
