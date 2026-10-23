from odoo import fields, models, _

class FxOutCloseMonthWizard(models.TransientModel):
    _name = "fx.out.close.month.wizard"
    _description = "Close Month - FX Out"

    month = fields.Date(required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one("account.journal", required=True)
    currency_id = fields.Many2one("res.currency", required=True)

    def action_close(self):
        closing = self.env["account.fx.out.closing"].create({
            "month": self.month,
            "journal_id": self.journal_id.id,
            "currency_id": self.currency_id.id,
        })
        closing.state = "done"
        return {"type": "ir.actions.act_window", "res_model": "account.fx.out.closing", "view_mode": "form", "res_id": closing.id}
