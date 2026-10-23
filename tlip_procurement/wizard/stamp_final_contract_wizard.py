from odoo import _, api, fields, models


class StampFinalContractWizard(models.TransientModel):
    _name = 'stamp.final.contract.wizard'
    _description = 'Stamp Final Contract'

    requisition_id = fields.Many2one('purchase.requisition', required=True)
    final_contract = fields.Many2one('ir.attachment', related='requisition_id.final_contract')
    new_contract_file = fields.Binary(string='New Contract File')
    new_contract_filename = fields.Char(string='Filename')

    def action_confirm(self):
        self.ensure_one()
        requisition = self.requisition_id

        if not self.new_contract_file:
            raise ValueError(_("Please upload a new contract file."))

        attachment = self.env['ir.attachment'].create({
            'name': self.new_contract_filename or f"{requisition.name}.pdf",
            'type': 'binary',
            'datas': self.new_contract_file,
            'res_model': requisition._name,
            'res_id': requisition.id,
            'mimetype': 'application/pdf',
        })
        old_final_contract = requisition.final_contract
        requisition.sudo().write({'final_contract': attachment.id})

        requisition.message_post(body=_("Final contract updated by %s", self.env.user.name), attachment_ids=[old_final_contract.id])
