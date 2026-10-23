from odoo import models, fields, api
from datetime import date, timedelta
import calendar

class FxOutRate(models.Model):
    _name = "account.fx.out.rate"
    _description = "FX Out Daily Rate"
    _rec_name = "display_name"

    company_id = fields.Many2one("res.company", required=True, ondelete="cascade")
    currency_id = fields.Many2one("res.currency", required=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    fx_out_ut = fields.Float(string="FX Out (Estimated)", digits=(16, 2))
    fx_out_ok = fields.Float(string="FX Out (Finalized)", digits=(16, 2))
    display_name = fields.Char(compute="_compute_display_name", store=True)
    temp_amount_residual = fields.Float(
        string="Prev Amt Residual (VND)",
        digits=(16, 2)
    )
    temp_amount_residual_currency = fields.Float(
        string="Prev Amt Residual (FC)",
        digits=(16, 2)
    )
    
    @api.depends("company_id", "currency_id", "date")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.company_id.name} - {rec.currency_id.name} - {rec.date}"

    @api.model
    def compute_monthly_fx_out(self, month, year):
        """
        End-of-month FX Recalculation Process (Per company)
        month = int (1-12)
        year  = int (YYYY)

        Steps:
            1. Determine date range (first_day → last_day)
            2. Loop all FC bank/cash accounts
            3. For each day:
                • compute FX_out_OK
                • update outbound payments of that account/day
                • rebuild journal entry + FX diff
        """

        # Convert to int if passed as string
        month = int(month)
        year = int(year)

        # Determine date range
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        company = self.env.company
        AccountPayment = self.env["account.payment"]

        # Collect all FX currencies used by company accounts
        fx_currencies = self._get_fx_currencies(company)
        for currency in fx_currencies:
            current_day = first_day
            while current_day <= last_day:

                # 1. Compute FX_out_OK
                fx_ok = self._calculate_fx_out(
                    company=company,
                    currency=currency,
                    target_date=current_day,
                    mode="ok",
                )

                # 2. Update outbound payments of this account/day
                payments = AccountPayment.search([
                    ("company_id", "=", company.id),
                    ("date", "=", current_day),
                    ("currency_id", "=", currency.id),
                    ("payment_type", "=", "outbound"),
                    ("state", "!=", "draft"),
                ])

                for p in payments:
                    if not p.move_id:
                        continue

                    # Update FX rate values
                    p.write({
                        "fx_out": fx_ok,
                        "entry_currency_rate": fx_ok,
                    })

                    # 3. Rebuild journal entry + FX diff
                    # remove old FX-diff entries if any
                    p._remove_currencydiff_entry()

                    # revert JE to draft
                    if p.move_id.state == "posted":
                        p.move_id.button_draft()

                    # re-generate JE core values
                    p._generate_journal_entry()

                    # post updated JE
                    p.move_id.action_post()

                    # 4. Recreate FX diff
                    p._generate_writeoff_journal_entry()
                
                    # 5. Re-link to vendor bill if needed
                    self._relink_payment_to_vendor_bill(p)

                current_day += timedelta(days=1)

        return True

    def _relink_payment_to_vendor_bill(self, payment):
        """
        Reconnect a payment to its vendor bill after FX recalculation.
        Only reconcile PAYABLE lines.
        """

        MoveLine = self.env["account.move.line"]

        # 1. Find vendor bills of this partner
        vendor_bills = self.env["account.move"].search([
            ("partner_id", "=", payment.partner_id.id),
            ("move_type", "=", "in_invoice"),
            ("state", "=", "posted"),
            ("company_id", "=", payment.company_id.id),
            ("payment_state", "!=", "paid"),
        ])

        if not vendor_bills:
            return False

        # 2. Get payment payable lines
        pay_lines = payment.move_id.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
                    and not l.reconciled
        )

        if not pay_lines:
            return False

        # 3. Try to reconcile with each bill
        for bill in vendor_bills:

            bill_lines = bill.line_ids.filtered(
                lambda l: l.account_id.account_type == "liability_payable"
                        and not l.reconciled
            )

            if not bill_lines:
                continue

            # Combine payment payable line + bill payable line
            lines_to_reconcile = pay_lines + bill_lines

            try:
                lines_to_reconcile.reconcile()
                return True
            except Exception:
                # Try next bill
                continue

        return False

    def _get_fx_currencies(self, company):
        accounts = self.env["account.account"].search([
            ("company_ids", "in", [company.id]),
            ("fx_currency_id", "!=", False),
        ])
        return accounts.mapped("fx_currency_id")

    def _calculate_fx_out(self, company, currency, target_date, mode="ut"):
        """
        FX Out calculation per FX currency (aggregated across all bank/cash accounts).

        This method intentionally differentiates between:
            • historical outbound payments (included in opening balance)
            • same-day outbound payments (excluded from today's activity)

        Formula:
            FX = (A + B) / (C + D)

        Where:
            A = accumulated amount_residual (VND) up to the previous day,
                INCLUDING outbound payments of previous days

            C = accumulated amount_residual_currency (FC) up to the previous day,
                INCLUDING outbound payments of previous days

            B = amount_residual (VND) of TODAY,
                EXCLUDING outbound payments of today

            D = amount_residual_currency (FC) of TODAY,
                EXCLUDING outbound payments of today

        Key business rules implemented:
            1. FX is calculated at currency level (not per bank account)
            2. Opening balance (A, C):
                - retrieved from the nearest previous FX record within the same month
                - outbound payments of that previous day are added back
            3. Today's activity (B, D):
                - excludes outbound payments because FX_out is applied AFTER calculation
            4. temp_amount_residual and temp_amount_residual_currency:
                - store cumulative balances for use by the next day
            5. Historical FX records may be updated to normalize outbound impact
                before continuing the calculation chain

        Filters applied:
            - company_id = company
            - currency_id = FX currency
            - move posted
            - date = previous days / today
        """


        AccountMoveLine = self.env["account.move.line"]

        # All bank/cash accounts with this FX currency
        accounts = self.env["account.account"].search([
            ("company_ids", "in", [company.id]),
            ("fx_currency_id", "=", currency.id),
        ])
        account_ids = accounts.ids

        # Opening balances
        prev_day = target_date - timedelta(days=1)
        A = 0.0  # prev residual VND
        C = 0.0  # prev residual FC

        # Allow fallback to previous month last day
        month_start = target_date.replace(day=1) - timedelta(days=3)

        # Only walk backward inside the same month
        search_day = prev_day
        prev_rec = False
        while search_day >= month_start:
            prev_rec = self.search([
                ("company_id", "=", company.id),
                ("currency_id", "=", currency.id),
                ("date", "=", search_day),
            ], limit=1)

            # Add outbound payments of THAT PREVIOUS DAY
            # because outbound was excluded when FX was computed
            # on that day, but must be included for next day opening
            if prev_rec and (
                (prev_rec.temp_amount_residual not in (None, 0.0)) or
                (prev_rec.temp_amount_residual_currency not in (None, 0.0))
            ):
                A = prev_rec.temp_amount_residual or 0.0
                C = prev_rec.temp_amount_residual_currency or 0.0

                # Add outbound of that day
                outbound = AccountMoveLine.search([
                    ("company_id", "=", company.id),
                    ("move_id.state", "=", "posted"),
                    ("account_id", "in", account_ids),
                    ("currency_id", "=", currency.id),
                    ("date", "=", search_day),
                    ("move_id.origin_payment_id.payment_type", "=", "outbound"),
                ])

                A += sum(outbound.mapped("amount_residual"))
                C += sum(outbound.mapped("amount_residual_currency"))
                
                # Normalize stored temp values for chain consistency
                prev_rec.write({
                    "temp_amount_residual": A,
                    "temp_amount_residual_currency": C,
                })
                break

            # Move backward 1 day
            search_day -= timedelta(days=1)


        # Today's activity
        # Exclude outbound payments of TODAY
        today_lines = AccountMoveLine.search([
            ("company_id", "=", company.id),
            ("move_id.state", "=", "posted"),
            ("account_id", "in", account_ids),
            ("currency_id", "=", currency.id),
            ("date", "=", target_date),
            ("move_id.origin_payment_id.payment_type", "!=", "outbound"),
        ])

        B = sum(today_lines.mapped("amount_residual"))
        D = sum(today_lines.mapped("amount_residual_currency"))

        denominator = C + D
        fx_value = (A + B) / denominator if denominator else 0.0

        # Save record
        rec = self.search([
            ("company_id", "=", company.id),
            ("currency_id", "=", currency.id),
            ("date", "=", target_date),
        ], limit=1)

        vals = {
            "company_id": company.id,
            "currency_id": currency.id,
            "date": target_date,
            "fx_out_ut" if mode == "ut" else "fx_out_ok": fx_value,
            
            # Save temp for next day
            "temp_amount_residual": A + B,
            "temp_amount_residual_currency": C + D,
        }

        if rec:
            rec.write(vals)
        else:
            rec = self.create(vals)

        return fx_value

