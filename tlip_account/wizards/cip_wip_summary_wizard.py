from odoo import api, fields, models, _


class CipWipSummaryWizard(models.TransientModel):
    _name = 'cip.wip.summary.wizard'
    _description = 'CIP/WIP Summary Report Wizard'

    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1)
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.today()
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    def action_view_report(self):
        """Open the pivot view with date filters applied"""
        self.ensure_one()

        # Build domain for filtering
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ]

        return {
            'name': _('CIP/WIP Summary: %s to %s') % (
                self.date_from.strftime('%Y-%m-%d'),
                self.date_to.strftime('%Y-%m-%d')
            ),
            'type': 'ir.actions.act_window',
            'res_model': 'cip.wip.summary',
            'view_mode': 'pivot,list,graph',
            'domain': domain,
            'context': {
                'search_default_group_account': 1,
                'search_default_group_project': 1,
                'date_from': self.date_from.strftime('%Y-%m-%d'),
            },
        }
