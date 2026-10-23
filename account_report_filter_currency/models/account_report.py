# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountReport(models.Model):
    _inherit = 'account.report'

    filter_currency = fields.Boolean(
        string="Currency",
        compute=lambda x: x._compute_report_option_filter('filter_currency'), readonly=False, store=True, depends=['root_report_id', 'section_main_report_ids'],
    )
    
    def _init_options_filter_currency(self, options, previous_options=None, additional_currency_domain=None):
        if not self.filter_currency:
            return

        options['filter_currency'] = True
        previous_currency_id = previous_options and [previous_options.get('currency_id', False)] or []

        selected_currency_id = [int(currency) for currency in previous_currency_id]
        # search instead of browse so that record rules apply and filter out the ones the user does not have access to
        selected_currency = selected_currency_id and self.env['res.currency'].with_context(
            active_test=False).search([('id', 'in', selected_currency_id)]) or self.env['res.currency']
        options['selected_currency_id'] = selected_currency.mapped('name')
        options['currency_id'] = selected_currency.id

    @api.model
    def _get_options_currency_domain(self, options):
        domain = []
        if options.get('currency_id'):
            currency_id = [int(options.get('currency_id'))]
            domain.append(('currency_id', 'in', currency_id))
        return domain

    def _get_options_domain(self, options, date_scope):
        self.ensure_one()
        domain = super()._get_options_domain(options, date_scope)

        # Get the currency that we need to filter on from the options and add a domain for them.
        domain += self._get_options_currency_domain(options)
        return domain
