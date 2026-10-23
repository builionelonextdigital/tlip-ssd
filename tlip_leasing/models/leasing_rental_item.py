from odoo import models, fields, api

class LeasingRentalItem(models.Model):
    _name = 'leasing.rental.item'
    _description = 'Rental Item'

    name = fields.Char('Item')
    agreement_id = fields.Many2one('leasing.agreement')
    supplement_id = fields.Many2one('leasing.supplement')
    termination_id = fields.Many2one('leasing.termination')
    line_number = fields.Integer('No.', compute='_compute_line_number')
    qty = fields.Float('Amount')
    description = fields.Char('Description')

    @api.depends('agreement_id.rental_item_ids', 'supplement_id.rental_item_ids', 'termination_id.rental_item_ids')
    def _compute_line_number(self):
        for record in self:
            leasing_rec = record.agreement_id or record.supplement_id or record.termination_id
            rental_items = leasing_rec.rental_item_ids
            record.line_number = rental_items._origin.ids.index(record._origin.id) + 1 if record._origin.id else 1
