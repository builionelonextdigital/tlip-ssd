from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    fx_in = fields.Float(string="FX In", digits=(16, 2), required=True)
    fx_out = fields.Float(string="FX Out", digits=(16, 2), tracking=True)

    def action_compute_fx_out(self):
        self.ensure_one()

        if self.payment_type != "outbound":
            raise UserError(_("Only outbound payments can compute FX Out."))

        company = self.company_id
        currency = self.currency_id
        payment_date = self.date
        fx_model = self.env["account.fx.out.rate"]

        # Compute fresh FX value for the day
        fx_value = fx_model._calculate_fx_out(company, currency, payment_date)

        # Update or create the daily FX record
        fx_record = fx_model.search([
            ("company_id", "=", company.id),
            ("currency_id", "=", currency.id),
            ("date", "=", payment_date),
        ], limit=1)

        if fx_record:
            fx_record.fx_out_ut = fx_value
        else:
            fx_model.create({
                "company_id": company.id,
                "currency_id": currency.id,
                "date": payment_date,
                "fx_out_ut": fx_value,
            })

        # Apply to all outbound payments of same day/currenc
        self.fx_out = fx_value
        self.entry_currency_rate = fx_value

        # Return onchange-like data to update UI instantly
        return {
            "value": {
                "fx_out": fx_value,
                "entry_currency_rate": fx_value,
            },
            "effect": {
                "fadeout": "fast",
                "message": _(f"FX Out {fx_value:.2f} applied for {payment_date}."),
                "type": "rainbow_man",
            }
        }


    def action_submit_approval(self):

        for rec in self:

            if (
                rec.payment_type == "inbound"
                and rec.currency_id.name != "VND"
                and rec.fx_in <= 0
            ):
                raise UserError(
                    _("FX In rate must be filled before submitting approval.")
                )

        return super().action_submit_approval()


    @api.depends(
        "amount",
        "currency_id",
        "foreign_currency_id",
        "company_id",
        "payment_type",
        "fx_in",
        "fx_out"
    )
    def _compute_entry_currency_rate(self):

        for rec in self:

            rate = 1

            # inbound → FX IN
            if rec.payment_type == "inbound" and rec.fx_in > 0:
                rate = rec.fx_in

            # outbound → FX OUT
            elif rec.payment_type == "outbound" and rec.fx_out > 0:
                rate = rec.fx_out

            rec.entry_currency_rate = rate



    @api.onchange("fx_in", "fx_out", "amount")
    def _onchange_fx_rate(self):
        for rec in self:
            if rec.payment_type == "inbound" and rec.fx_in:
                rec.entry_currency_rate = rec.fx_in
            if rec.payment_type == "outbound" and rec.fx_out:
                rec.entry_currency_rate = rec.fx_out