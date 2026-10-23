from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class LeasingAgreement(models.Model):
    _name = 'leasing.agreement'
    _inherit = 'leasing.agreement.base'
    _description = 'Agreement'

    agreement_type = fields.Selection(selection=[
        ('reservation', 'Reservation'),
        ('contract', 'Contract')
    ])
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('wait_for_approval', 'Waiting for Approval'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('complete', 'Completed'),
        ('terminate', 'Terminated'),
        ('cancel', 'Cancelled')
    ], default='draft')
    agreement_id = fields.Many2one('leasing.agreement')
    origin_agreement_type = fields.Selection(
        related='agreement_id.agreement_type', readonly=True)
    contract_ids = fields.One2many('leasing.agreement', 'agreement_id', domain=[
                                   ('agreement_type', '=', 'contract')])
    contract_count = fields.Integer(compute='_compute_agreement_count')
    agreement_expiry_date = fields.Date(
        related='agreement_id.expiry_date', readonly=True)
    supplement_agreement_ids = fields.One2many(
        'leasing.supplement', 'agreement_id')
    termination_agreement_ids = fields.One2many(
        'leasing.termination', 'agreement_id')
    supplement_agreement_count = fields.Integer(
        compute='_compute_agreement_count')
    termination_agreement_count = fields.Integer(
        compute='_compute_agreement_count')
    contract_type_id = fields.Many2one('contract.type', 'Contract Type')
    contract_type_classification = fields.Selection(
        related='contract_type_id.classification')
    rental_item_ids = fields.One2many('leasing.rental.item', 'agreement_id')
    rental_fee_ids = fields.One2many(
        'leasing.rental.fee', 'agreement_id', string='Rental Fees')
    total_fee_amount = fields.Monetary(
        'Total Price', compute='_compute_fee_amount')
    due_date = fields.Integer(string='Due Date')

    def _compute_agreement_count(self):
        for record in self:
            supplements = record.quotation_id.supplement_agreement_ids.filtered(
                lambda r: r.agreement_type == record.agreement_type)
            terminations = record.quotation_id.termination_agreement_ids.filtered(
                lambda r: r.agreement_type == record.agreement_type)
            record.contract_count = len(record.contract_ids)
            record.supplement_agreement_count = len(supplements)
            record.termination_agreement_count = len(terminations)

    @api.depends('rental_fee_ids', 'rental_fee_ids.amount')
    def _compute_fee_amount(self):
        for record in self:
            record.total_fee_amount = sum(
                record.rental_fee_ids.mapped('amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            agreement_type = vals.get('agreement_type')
            if not 'name' in vals:
                if agreement_type == 'reservation':
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'reservation.agreement.sequence') or _('/')
                elif agreement_type == 'contract':
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'lease.contract.sequence') or _('/')
        return super().create(vals_list)

    def action_create_contract(self):
        self.ensure_one()
        existing_contract = self._existing_contract()
        if existing_contract:
            if existing_contract[:1].state != 'draft':
                raise UserError(
                    _("There is already an in-progress Lease Contract"))
        else:
            contract_vals = self._prepare_contract_vals()
            self.env['leasing.agreement'].create(contract_vals)
        return self.with_context(show_existing_agreement=True).action_get_contract_view()

    def action_terminate(self):
        self.write({
            'active': False,
            'state': 'terminate'
        })

    def action_payment(self):
        # TODO: It's for testing now, new payment flow is waiting for requirements
        self._post_process_payment()

    def _post_process_payment(self):
        # TODO: waiting for requirements
        self.ensure_one()
        self.payment_state = 'paid'
        self.state = 'complete'

    def _prepare_contract_vals(self):
        self.ensure_one()
        vals = self._prepare_common_agreement_vals()
        vals.update({
            'agreement_type': 'contract',
            'quotation_id': self.quotation_id.id,
        })
        return vals

    def _prepare_common_agreement_vals(self):
        self.ensure_one()
        return {
            'agreement_id': self.id,
            'lessor_id': self.lessor_id.id,
            'lessor_street': self.lessor_street,
            'lessor_street_2': self.lessor_street_2,
            'lessor_district_id': self.lessor_district_id.id,
            'lessor_ward_id': self.lessor_ward_id.id,
            'lessor_state_id': self.lessor_state_id.id,
            'lessor_country_id': self.lessor_country_id.id,
            'lessee_id': self.lessee_id.id,
            'lessee_name': self.lessee_name,
            'lessee_email': self.lessee_email,
            'lessee_phone': self.lessee_phone,
            'lessee_street': self.lessee_street,
            'lessee_street_2': self.lessee_street_2,
            'lessee_district_id': self.lessee_district_id.id,
            'lessee_ward_id': self.lessee_ward_id.id,
            'lessee_state_id': self.lessee_state_id.id,
            'lessee_country_id': self.lessee_country_id.id,
            'lessee_title_id': self.lessee_title_id.id,
            'lessor_legal_id': self.lessor_legal_id.id,
            'lessor_legal_title_id': self.lessor_legal_title_id.id,
            'lessor_legal_email': self.lessor_legal_email,
            'lessor_legal_fax': self.lessor_legal_fax,
            'lessor_legal_phone': self.lessor_legal_phone,
            'lessor_legal_vat': self.lessor_legal_vat,
            'lessor_legal_account_number': self.lessor_legal_account_number,
            'lessor_legal_bank_id': self.lessor_legal_bank_id.id,
            'lessee_legal_id': self.lessee_legal_id.id,
            'lessee_legal_title_id': self.lessee_legal_title_id.id,
            'lessee_legal_email': self.lessee_legal_email,
            'lessee_legal_fax': self.lessee_legal_fax,
            'lessee_legal_phone': self.lessee_legal_phone,
            'lessee_legal_vat': self.lessee_legal_vat,
            'lessee_legal_account_number': self.lessee_legal_account_number,
            'lessee_legal_bank_id': self.lessee_legal_bank_id.id,
            'land_plot_id': self.land_plot_id.id,
            'plot_view_id': self.plot_view_id.id,
            'land_plot_category_id': self.land_plot_category_id.id,
            'area': self.area,
            'actual_area': self.actual_area,
            'rental_fee': self.rental_fee,
            'reservation_deposit': self.reservation_deposit,
            'reservation_deposit_amount': self.reservation_deposit_amount,
            'exchange_rate_amount': self.exchange_rate_amount,
            'rental_fee_unit': self.rental_fee_unit,
            'reservation_deposit_type': self.reservation_deposit_type,
            'commence_date': self.commence_date,
            'commence_time': self.commence_time,
            'expiry_date': self.expiry_date,
            'expiry_time': self.expiry_time,
            'adjusted_fee_amount': self.adjusted_fee_amount,
            'investment_certificate_no': self.investment_certificate_no,
            'investment_certificate_date': self.investment_certificate_date,
            'enterprise_certificate_no': self.enterprise_certificate_no,
            'enterprise_certificate_date': self.enterprise_certificate_date,
            'standard_factory_no': self.standard_factory_no,
            'standard_factory_date': self.standard_factory_date,
            'map_no': self.map_no,
            'land_rights_no': self.land_rights_no,
            'land_rights_restriction': self.land_rights_restriction,
            'other_detail': self.other_detail,
            'private_use_area': self.private_use_area,
            'common_use_area': self.common_use_area,
            'land_use_term': self.land_use_term,
            'usage_capacity': self.usage_capacity,
            'number_of_spot': self.number_of_spot,
            'using_purpose': self.using_purpose,
            'lease_term_year': self.lease_term_year,
            'lease_term_month': self.lease_term_month,
            'max_industrial_water': self.max_industrial_water,
            'max_electricity': self.max_electricity,
            'payment_frequency': self.payment_frequency,
            'payment_term': self.payment_term,
            'area_tolerance_within': self.area_tolerance_within,
            'area_tolerance_exceed': self.area_tolerance_exceed,
            'price_adjusted': self.price_adjusted,
            'construction_date_from': self.construction_date_from,
            'construction_date_to': self.construction_date_to,
            'installation_date_from': self.installation_date_from,
            'installation_date_to': self.installation_date_to,
            'trial_production_date_from': self.trial_production_date_from,
            'trial_production_date_to': self.trial_production_date_to,
            'official_production_date': self.official_production_date,
            'handover_date': self.handover_date,
            'using_time': self.using_time,
            'revenue_sharing_ratio': self.revenue_sharing_ratio
        }

    def _prepare_supplement_vals(self):
        vals = self._prepare_common_agreement_vals()
        vals.update({
            'rental_fee': self.rental_fee,
            'reservation_deposit': self.reservation_deposit,
            'reservation_deposit_amount': self.reservation_deposit_amount,
            'exchange_rate_amount': self.exchange_rate_amount,
            'rental_fee_unit': self.rental_fee_unit,
            'reservation_deposit_type': self.reservation_deposit_type,
            'rental_fee_ids': [Command.create({
                'fee_type_id': r.fee_type_id.id,
                'amount': r.amount,
                'date_from': r.date_from,
                'date_to': r.date_to,
                'location_start': r.location_start,
                'location_end': r.location_end,
                'number_of_pipes': r.number_of_pipes,
                'telecom_line_length': r.telecom_line_length,
                'premium_excluded_vat': r.premium_excluded_vat
            }) for r in self.rental_fee_ids],
            'rental_item_ids': [Command.create({
                'name': r.name,
                'qty': r.qty,
                'description': r.description
            }) for r in self.rental_item_ids]
        })
        if self.env.context.get('is_tariff'):
            vals['is_tariff'] = True

        return vals

    def _prepare_termination_vals(self):
        vals = self._prepare_common_agreement_vals()
        vals.update({
            'rental_fee': self.rental_fee,
            'reservation_deposit': self.reservation_deposit,
            'reservation_deposit_amount': self.reservation_deposit_amount,
            'exchange_rate_amount': self.exchange_rate_amount,
            'rental_fee_unit': self.rental_fee_unit,
            'reservation_deposit_type': self.reservation_deposit_type,
            'rental_fee_ids': [Command.create({
                'fee_type_id': r.fee_type_id.id,
                'amount': r.amount,
                'date_from': r.date_from,
                'date_to': r.date_to,
                'location_start': r.location_start,
                'location_end': r.location_end,
                'number_of_pipes': r.number_of_pipes,
                'telecom_line_length': r.telecom_line_length,
                'premium_excluded_vat': r.premium_excluded_vat
            }) for r in self.rental_fee_ids],
            'rental_item_ids': [Command.create({
                'name': r.name,
                'qty': r.qty,
                'description': r.description
            }) for r in self.rental_item_ids]
        })
        return vals

    def action_create_supplemental_agreement(self):
        self.ensure_one()
        existing_supplement = self._existing_supplement()
        if existing_supplement:
            if existing_supplement[:1].state != 'draft':
                raise UserError(
                    _("There is already an in-progress Supplemental Agreement"))
            return self.with_context(show_existing_agreement=True).action_get_supplement_agreement_view()

        supplement_vals = self._prepare_supplement_vals()
        self.env['leasing.supplement'].create([supplement_vals])
        return self.with_context(show_existing_agreement=True).action_get_supplement_agreement_view()

    def action_create_tariff(self):
        return self.with_context(is_tariff=True).action_create_supplemental_agreement()

    def action_create_termination_agreement(self):
        self.ensure_one()
        existing_termination = self._existing_termination()
        if existing_termination:
            if existing_termination[:1].state != 'draft':
                raise UserError(
                    _("There is already an in-progress Termination Agreement"))
            return self.with_context(show_existing_agreement=True).action_get_termination_agreement_view()

        termination_vals = self._prepare_termination_vals()
        self.env['leasing.termination'].create([termination_vals])
        return self.with_context(show_existing_agreement=True).action_get_termination_agreement_view()

    def action_get_agreement_view(self):
        self.ensure_one()
        if self.agreement_id.agreement_type == 'reservation':
            action = self.env['ir.actions.act_window']._for_xml_id(
                'tlip_leasing.action_reservation_agreement_view')
            view = self.env.ref('tlip_leasing.reservation_agreement_view_form')
        else:
            action = self.env['ir.actions.act_window']._for_xml_id(
                'tlip_leasing.action_contract_agreement_view')
            view = self.env.ref('tlip_leasing.contract_agreement_view_form')

        action.update({
            'views': [(view.id, 'form')],
            'target': 'current',
            'res_id': self.agreement_id.id
        })
        return action

    def action_get_contract_view(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.action_contract_agreement_view')
        action['domain'] = [
            ('agreement_id', '=', self.id),
            ('agreement_type', '=', 'contract')
        ]
        if self.env.context.get('show_existing_agreement'):
            action.update({
                'views': [(self.env.ref('tlip_leasing.contract_agreement_view_form').id, 'form')],
                'target': 'current',
                'res_id': self._existing_contract().id
            })
        return action

    def action_get_supplement_agreement_view(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.action_supplemental_agreement_view')
        action['domain'] = [
            ('quotation_id', '=', self.quotation_id.id),
            ('agreement_id.agreement_type', '=', self.agreement_type)
        ]
        if self.env.context.get('show_existing_agreement'):
            action.update({
                'views': [(self.env.ref('tlip_leasing.supplemental_agreement_view_form').id, 'form')],
                'target': 'current',
                'res_id': self._existing_supplement().id
            })
        return action

    def action_get_termination_agreement_view(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'tlip_leasing.action_termination_agreement_view')
        action['domain'] = [
            ('quotation_id', '=', self.quotation_id.id),
            ('agreement_id.agreement_type', '=', self.agreement_type)
        ]
        if self.env.context.get('show_existing_agreement'):
            action.update({
                'views': [(self.env.ref('tlip_leasing.termination_agreement_view_form').id, 'form')],
                'target': 'current',
                'res_id': self._existing_termination().id
            })
        return action

    def action_print(self):
        self.ensure_one()
        docx_template = self.contract_type_id.document_template_id
        ctx = {
            'menu_action_id': docx_template.id,
            'active_ids': self.ids,
            'active_model': self._name
        }
        return self.env['docx.template'].with_context(**ctx).make_docx_pdf_report()

    def _existing_contract(self):
        self.ensure_one()
        return self.contract_ids.filtered(lambda r: r.state in ('draft', 'wait'))[:1]

    def _existing_supplement(self):
        self.ensure_one()
        return self.supplement_agreement_ids.filtered(lambda r: r.state in ('draft', 'wait'))

    def _existing_termination(self):
        self.ensure_one()
        return self.termination_agreement_ids.filtered(lambda r: r.state in ('draft', 'wait'))

    def _trigger_action_approve(self):
        result = super()._trigger_action_approve()
        return result

    def _trigger_action_refuse(self):
        result = super()._trigger_action_refuse()
        return result

    def _trigger_action_after_submit(self, request):
        result = super()._trigger_action_after_submit(request=request)
        self.write({
            'state': 'wait_for_approval',
        })
        return result

    def _trigger_action_withdraw(self, reason: str):
        self.action_cancel()
        super()._trigger_action_withdraw(reason)
