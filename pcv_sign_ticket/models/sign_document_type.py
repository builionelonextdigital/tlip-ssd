from odoo import api, fields, models


class SignDocumentType(models.Model):
    _name = "sign.document.type"
    _description = "Sign Document Type"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one('ir.model', string="Related Model")
    deadline_days = fields.Integer(
        string="Deadline (days)",
        default=7,
        help="Number of days from ticket creation until the signing deadline.",
    )
    use_cell_positioning = fields.Boolean(
        string="Use Cell Positioning",
        default=False,
        help="When enabled, the system automatically aligns the next signature "
             "on the next cell using the placeholder text. "
             "When disabled, signers must follow the [signer1], [signer2], ... convention.",
    )
    placeholder_text = fields.Char(string="Placeholder Text")

    @api.onchange("use_cell_positioning")
    def _onchange_use_cell_positioning(self):
        if not self.use_cell_positioning:
            self.placeholder_text = False
