from odoo import fields, models, _

class FxOutCalcUTWizard(models.TransientModel):
    _name = "fx.out.calc.ut.wizard"
    _description = "Calculate FX Out UT Wizard"

    date = fields.Date(required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one("account.journal", required=True)
    currency_id = fields.Many2one("res.currency", required=True)

    def action_calculate(self):
        rate = self.env["account.fx.out.rate"].search([
            ("date", "=", self.date),
            ("journal_id", "=", self.journal_id.id),
            ("currency_id", "=", self.currency_id.id),
        ], limit=1)
        if not rate:
            rate = self.env["account.fx.out.rate"].create({
                "date": self.date,
                "journal_id": self.journal_id.id,
                "currency_id": self.currency_id.id,
                "company_id": self.env.company.id,
            })
        rate.rate_ut = rate.compute_rate_by_formula()
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {"title": f"FX_out_UT = {rate.rate_ut}", "type": "success"}}
