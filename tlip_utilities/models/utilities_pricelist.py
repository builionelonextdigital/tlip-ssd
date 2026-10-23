from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UtilitiesPricelist(models.Model):
    _name = 'utilities.pricelist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Utilities Pricelist'

    name = fields.Char(required=True, tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirm')], string="State",
        default='draft', tracking=True, required=True)
    utility_type = fields.Selection(
        [('electricity', 'Electricity'),
         ('water', 'Water')], required=True, string="Utility Type")
    partner_ids = fields.Many2many('res.partner', 'Customers')
    development_phase_ids = fields.Many2many('development.phase', string='Phases')
    currency_id = fields.Many2one(
        'res.currency', required=True, tracking=True)
    date_from = fields.Datetime(required=True, tracking=True)
    date_to = fields.Datetime(required=True, tracking=True)
    pricelist_item_ids = fields.One2many(
        'utilities.pricelist.item', 'pricelist_id', 'Price Rules')
    # Electricity
    electricity_type = fields.Selection(
        [('normal', 'Normal'),
         ('solar', 'Solar')], string="Electricity Type",
        default='normal', required=True)
    electricity_categ_id = fields.Many2one(
        'electricity.category', string='Electricity Category',
        tracking=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        if any(record.date_from > record.date_to for record in self):
            raise ValidationError(_("Start date should precede the end date."))

    def action_confirm(self):
        self.state = 'confirm'

    def action_reset(self):
        self.state = 'draft'

    def action_send_by_email(self):
        self.ensure_one()
        template_id = False
        default_template_id = template_id

        partner_to = False
        email_to = False

        ctx = {
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_light",
            'default_model': 'utilities.pricelist',
            'default_res_ids': self.ids,
            'default_template_id': default_template_id,
            'default_record_name': 'Send Pricelist',
            'partner_to': partner_to and partner_to.id or False,
            'email_to': email_to or False,
            'mail_post_autofollow': False,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [[False, 'form']],
            'target': 'new',
            'context': ctx,
        }
