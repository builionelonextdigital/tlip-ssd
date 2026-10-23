from odoo import models, fields, api, Command, _
from odoo.tools import format_date, format_datetime
from odoo.exceptions import UserError


class LeasingSupplement(models.Model):
    _name = 'leasing.supplement'
    _inherit = 'leasing.agreement.base'
    _description = 'Supplemental Agreement'

    is_tariff = fields.Boolean(default=False)
    agreement_id = fields.Many2one(
        'leasing.agreement', required=True, copy=False)
    agreement_type = fields.Selection(
        related='agreement_id.agreement_type', readonly=True)
    contract_type_id = fields.Many2one(
        'contract.type', related='agreement_id.contract_type_id', readonly=True)
    contract_type_classification = fields.Selection(
        related='contract_type_id.classification', readonly=True)
    quotation_id = fields.Many2one(
        'leasing.quotation', related='agreement_id.quotation_id', readonly=True)
    reason = fields.Text('Reason for change')
    effective_date = fields.Date('Effective Date')
    summary_change_ids = fields.One2many(
        'leasing.summary.changes', 'supplement_agreement_id', string="Changes")
    rental_fee_ids = fields.One2many(
        'leasing.rental.fee', 'supplement_id', string='Rental Fees')
    rental_item_ids = fields.One2many('leasing.rental.item', 'supplement_id')
    total_fee_amount = fields.Monetary(
        'Total Price', compute='_compute_fee_amount')
    agreement_expiry_date = fields.Date(
        related='agreement_id.expiry_date', readonly=True)

    @api.depends('rental_fee_ids', 'rental_fee_ids.amount')
    def _compute_fee_amount(self):
        for record in self:
            record.total_fee_amount = sum(
                record.rental_fee_ids.mapped('amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals:
                agreement = self.env['leasing.agreement'].browse(vals.get('agreement_id'))
                code = self.env['ir.sequence'].next_by_code(
                    'supplemental.agreement.sequence') or _('/')
                vals['name'] = f"{agreement.name}-{code}"
        records = super().create(vals_list)
        return records

    def action_get_agreement_view(self):
        self.ensure_one()
        if self.agreement_id.agreement_type == 'reservation':
            action = self.env['ir.actions.act_window']._for_xml_id('tlip_leasing.action_reservation_agreement_view')
            view = self.env.ref('tlip_leasing.reservation_agreement_view_form')
        else:
            action = self.env['ir.actions.act_window']._for_xml_id('tlip_leasing.action_contract_agreement_view')
            view = self.env.ref('tlip_leasing.contract_agreement_view_form')
        
        action.update({
            'views': [(view.id, 'form')],
            'target': 'current',
            'res_id': self.agreement_id.id
        })
        return action

    def _fields_tracking_change(self):
        return [
            'lessor_id',
            'lessor_street',
            'lessor_street_2',
            'lessor_district_id',
            'lessor_ward_id',
            'lessor_state_id',
            'lessor_country_id',
            'lessee_id',
            'lessee_name',
            'lessee_email',
            'lessee_phone',
            'lessee_street',
            'lessee_street_2',
            'lessee_district_id',
            'lessee_ward_id',
            'lessee_state_id',
            'lessee_country_id',
            'lessee_title_id',
            'lessor_legal_id',
            'lessor_legal_title_id',
            'lessor_legal_email',
            'lessor_legal_fax',
            'lessor_legal_phone',
            'lessor_legal_vat',
            'lessor_legal_account_number',
            'lessor_legal_bank_id',
            'lessee_legal_id',
            'lessee_legal_title_id',
            'lessee_legal_email',
            'lessee_legal_fax',
            'lessee_legal_phone',
            'lessee_legal_vat',
            'lessee_legal_account_number',
            'lessee_legal_bank_id',
            'commence_date',
            'commence_time',
            'expiry_date',
            'expiry_time',
            'land_plot_id',
            'land_plot_category_id',
            'area',
            'actual_area',
            'rental_fee',
            'reservation_deposit',
            'reservation_deposit_amount',
            'exchange_rate_amount',
            'rental_fee_unit',
            'reservation_deposit_type',
            'rental_fee_ids',
            'adjusted_fee_amount',
            'investment_certificate_no',
            'investment_certificate_date',
            'enterprise_certificate_no',
            'enterprise_certificate_date',
            'standard_factory_no',
            'standard_factory_date',
            'map_no',
            'land_rights_no',
            'land_rights_restriction',
            'other_detail',
            'private_use_area',
            'common_use_area',
            'land_use_term',
            'usage_capacity',
            'number_of_spot',
            'using_purpose',
            'lease_term_year',
            'lease_term_month',
            'max_industrial_water',
            'max_electricity',
            'payment_frequency',
            'payment_term',
            'area_tolerance_within',
            'area_tolerance_exceed',
            'price_adjusted',
            'construction_date_from',
            'construction_date_to',
            'installation_date_from',
            'installation_date_to',
            'trial_production_date_from',
            'trial_production_date_to',
            'official_production_date',
            'handover_date',
            'using_time',
            'revenue_sharing_ratio'
        ]

    @api.model
    def _check_records_have_change(self, current_many_vals, new_many_vals):
        if len(current_many_vals) != len(new_many_vals):
            return True

        fields_to_compare = [
            name for name, field in current_many_vals._fields.items()
            if field.store and field.copy and not field.automatic
        ]

        for current, new in zip(current_many_vals, new_many_vals):
            if any(current[field] != new[field] for field in fields_to_compare):
                return True

        return False

    def _get_difference_agreement_changes(self):
        self.ensure_one()

        reservation_agreement = self.agreement_id
        summary_change_vals = [Command.create({
            'name': change.name,
            'current_value': change.current_value,
            'new_value': change.new_value,
            'bypass_create': True
        }) for change in self.summary_change_ids]

        tracking_fields = self._fields_tracking_change()
        fields_to_compare = {name: field
                             for name, field in self.env[self._name]._fields.items() if name in tracking_fields}

        for name, field in fields_to_compare.items():
            current_val = reservation_agreement[name]
            new_val = self[name]
            field_name = field.get_description(self.env).get('string')

            if field.type in ('one2many', 'many2many'):
                if self._check_records_have_change(current_val, new_val):
                    summary_change_vals.append(Command.create({
                        'name': field_name,
                        'new_value': f'{field_name} changed'
                    }))
            elif current_val != new_val:
                if field.type == 'date':
                    current_val = format_date(self.env, current_val)
                    new_val = format_date(self.env, new_val)
                elif field.type == 'datetime':
                    current_val = format_datetime(self.env, current_val)
                    new_val = format_datetime(self.env, new_val)
                else:
                    current_val = field.convert_to_export(
                        current_val, reservation_agreement)
                    new_val = field.convert_to_export(new_val, self)

                summary_change_vals.append(Command.create({
                    'name': field_name,
                    'current_value': current_val,
                    'new_value': new_val
                }))

        return summary_change_vals

    def action_submit_changes(self):
        self.ensure_one()
        if not (self.effective_date and self.reason):
            raise UserError(
                _('Please select an effective date and provide a reason for the change.'))

        summary_change_vals = self._get_difference_agreement_changes()
        wizard = self.env['summary.change.wizard'].create([{
            'supplement_agreement_id': self.id,
            'change_line_ids': summary_change_vals
        }])
        return {
            'name': _("Summary of changes"),
            'view_mode': 'form',
            'view_id': self.env.ref('tlip_leasing.summary_change_wizard_view_form').id,
            'view_type': 'form',
            'res_model': 'summary.change.wizard',
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def _prepare_agreement_adjustment_values(self):
        self.ensure_one()
        vals = {
            'quotation_id': self.agreement_id.quotation_id.id,
            'agreement_type': self.agreement_id.agreement_type,
            'contract_type_id': self.agreement_id.contract_type_id.id,
            'name': self.agreement_id.name,
            'issued_date': self.agreement_id.issued_date,
            'expiry_date': self.agreement_id.expiry_date,
            'state': 'approve'
        }
        for field in self._fields_tracking_change():
            field_type = self._fields[field].type
            if field_type == 'many2one':
                vals[field] = self[field].id if self[field] else False
            elif field_type == 'one2many':
                vals[field] = [Command.create({
                    key: getattr(line, key)
                    for key in line._fields.keys()
                }) for line in self[field]]
            else:
                vals[field] = self[field]

        return vals

    def _action_effective(self):
        self.ensure_one()
        vals = self._prepare_agreement_adjustment_values()
        vals['name'] = self.agreement_id.name
        new_agreement = self.env['leasing.agreement'].create(vals)

        old_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', self.agreement_id._name), 
            ('res_id', 'in', self.agreement_id.ids)
        ])
        new_attachment_vals = []
        for attachment in old_attachments:
            new_attachment_vals.append({
                'res_model': new_agreement._name,
                'res_id': new_agreement.id,
                'name': attachment.name,
                'type': attachment.type,
                'datas': attachment.datas,
            })
        
        if new_attachment_vals:
            self.env['ir.attachment'].create(new_attachment_vals)

        self.agreement_id.action_archive()

    def action_complete(self):
        today = fields.Date.today()
        self.write({
            'state': 'complete'
        })
        for record in self.filtered(lambda r: r.effective_date <= today):
            record._action_effective()

    @api.model
    def cron_activate_supplement_agreements(self):
        today = fields.Date.today()
        supplement_agreements = self.env['leasing.supplement'].search([
            ('active', '=', True),
            ('effective_date', '<=', today),
            ('state', '=', 'complete')
        ])
        for record in supplement_agreements:
            record._action_effective()
