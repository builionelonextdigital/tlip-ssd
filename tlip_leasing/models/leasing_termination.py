from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LeasingTermination(models.Model):
    _name = 'leasing.termination'
    _inherit = 'leasing.agreement.base'
    _description = 'Termination Agreement'

    agreement_id = fields.Many2one('leasing.agreement', required=True, copy=False)
    quotation_id  = fields.Many2one('leasing.quotation', related='agreement_id.quotation_id', readonly=True)
    agreement_type = fields.Selection(
        related='agreement_id.agreement_type', readonly=True)
    contract_type_id = fields.Many2one(
        'contract.type', related='agreement_id.contract_type_id', readonly=True)
    contract_type_classification = fields.Selection(
        related='contract_type_id.classification', readonly=True)
    reason = fields.Text('Reason for change')
    terminated_date = fields.Date('Terminated Date')
    rental_fee_ids = fields.One2many(
        'leasing.rental.fee', 'termination_id', string='Rental Fees')
    total_fee_amount = fields.Monetary(
        'Total Price', compute='_compute_fee_amount')
    rental_item_ids = fields.One2many('leasing.rental.item', 'termination_id')

    @api.depends('rental_fee_ids', 'rental_fee_ids.amount')
    def _compute_fee_amount(self):
        for record in self:
            record.total_fee_amount = sum(
                record.rental_fee_ids.mapped('amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not 'name' in vals:
                agreement = self.env['leasing.agreement'].browse(vals.get('agreement_id'))
                code = self.env['ir.sequence'].next_by_code(
                    'termination.agreement.sequence') or _('/')
                vals['name'] = f"{agreement.name}-{code}"
        records = super().create(vals_list)
        return records
    
    def action_submit_approval(self):
        if not (self.terminated_date and self.reason and self.issued_date):
            raise UserError(_("Please provide information about Issued Date/Terminated Date and reason for termination request"))
        return super().action_submit_approval()
    
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
    
    def action_complete(self):
        today = fields.Date.today()
        self.write({
            'state': 'complete'
        })
        for record in self.filtered(lambda r: r.terminated_date <= today):
            record.agreement_id.action_terminate()

    @api.model
    def cron_activate_termination_agreements(self):
        today = fields.Date.today()
        termination_agreements = self.env['leasing.termination'].search([
            ('active', '=', True),
            ('state', '=', 'complete'),
            ('terminated_date', '<=', today)
        ])
        termination_agreements.agreement_id.action_terminate()
