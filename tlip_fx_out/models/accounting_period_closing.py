from odoo import api, models, _
from odoo.exceptions import UserError


class AccountingPeriodClosingFX(models.Model):
    _inherit = "accounting.period.closing"

    def action_adjust_fx_monthly(self):
        """
        Trigger Monthly FX-Out recalculation using fx_out_ok.
        """
        self.ensure_one()

        if self.state != "open":
            raise UserError(_("You can only adjust FX when the period is OPEN."))

        if not self.month or not self.year:
            raise UserError(_("Month and Year must be selected."))

        month = int(self.month)
        year = int(self.year)

        FxOut = self.env["account.fx.out.rate"]

        # Use context company
        FxOut = FxOut.with_company(self.company_id)

        # Run recalculation
        FxOut.compute_monthly_fx_out(month=month, year=year)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("FX Adjustment Completed"),
                "message": _("FX Out recalculated for %02d/%s." % (month, year)),
                "type": "success",
                "sticky": False,
            }
        }
