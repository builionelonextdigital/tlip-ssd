"""O2C No. 1 - Approved RFPs are not posted before the customer pays.

Acceptance criteria (tracker "Chi tiết task" / Tai-hien-issue O2C No.1 step D1-D4):
  D2  An approved, not yet posted RFP can be selected on an inbound payment
      with the amount allocated to it.
  D3  Confirming the payment posts the RFP (accounting date follows the rule
      of its Request Type) and reconciles it in the same step.
  D4  A posted invoice/RFP whose e-invoice is published cannot be reset to
      draft, also when button_draft is called from code/RPC (issue step C3).
"""
from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestO2CNo1RfpPayment(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.currency = cls.company.currency_id
        cls.today = fields.Date.context_today(cls.env["account.move"])
        cls.month_start = cls.today.replace(day=1)

        # tlip_account._post requires an open accounting period for the company.
        cls.env["accounting.period.closing"].create({
            "month": str(cls.today.month),
            "year": str(cls.today.year),
            "state": "open",
            "company_id": cls.company.id,
        })

        cls.type_payment_date = cls._create_invoice_type("MF: Management fee", "payment_date")
        cls.type_rfp_date = cls._create_invoice_type("LAND Business", "rfp_date")
        cls.type_period_end = cls._create_invoice_type("RBF: Ready-built factory rent", "period_end")

        groups = cls.env.ref("account.group_account_user")
        tlip_accountant = cls.env.ref("tlip_access_rights.group_tlip_accountant", raise_if_not_found=False)
        if tlip_accountant:
            groups |= tlip_accountant
        cls.bank_accountant = cls.env["res.users"].create({
            "name": "Test Bank Accountant",
            "login": "test_o2c1_bank_accountant",
            "company_id": cls.company.id,
            "company_ids": [Command.set(cls.company.ids)],
            "groups_id": [Command.set((groups | cls.env.ref("base.group_user")).ids)],
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def _create_invoice_type(cls, name, rule):
        return cls.env["invoice.type"].create({
            "name_en": name,
            "name_vn": name,
            "type": "service",
            "accounting_date_rule": rule,
        })

    @classmethod
    def _create_rfp(cls, amount, partner=None, invoice_type=None, approved=True, invoice_date=None):
        rfp = cls.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": (partner or cls.partner_a).id,
            "invoice_date": invoice_date or cls.month_start,
            "is_request_payment": True,
            "invoice_type_id": (invoice_type or cls.type_payment_date).id,
            "journal_id": cls.company_data["default_journal_sale"].id,
            "invoice_line_ids": [Command.create({
                "name": "Management fee",
                "quantity": 1,
                "price_unit": amount,
                "account_id": cls.company_data["default_account_revenue"].id,
                "tax_ids": [Command.clear()],
            })],
        })
        if approved:
            # Test fixture: outcome of the sales approval round (PIC submit -> manager approve).
            rfp.write({"approval_state": "approved"})
        return rfp

    def _create_payment(self, amount, rfp_allocations=(), partner=None, date=None, user=None):
        env = self.env(user=user) if user else self.env
        return env["account.payment"].create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": (partner or self.partner_a).id,
            "amount": amount,
            "date": date or self.today,
            "journal_id": self.company_data["default_journal_bank"].id,
            "rfp_line_ids": [
                Command.create({"move_id": rfp.id, "amount": alloc, "sequence": seq})
                for seq, (rfp, alloc) in enumerate(rfp_allocations)
            ],
        })

    # ------------------------------------------------------------------
    # D2 - selection on the payment
    # ------------------------------------------------------------------
    def test_approved_draft_rfp_is_available_on_inbound_payment(self):
        approved = self._create_rfp(145_200_000)
        not_approved = self._create_rfp(1_000, approved=False)
        other_customer = self._create_rfp(2_000, partner=self.partner_b)

        payment = self._create_payment(145_200_000)

        self.assertEqual(approved.state, "draft")
        self.assertIn(approved, payment.available_rfp_move_ids)
        self.assertNotIn(not_approved, payment.available_rfp_move_ids)
        self.assertNotIn(other_customer, payment.available_rfp_move_ids)

    def test_rfp_of_other_company_is_not_available(self):
        company_2 = self.setup_other_company(name="TLIP company 2")["company"]
        rfp_company_2 = self.env["account.move"].with_company(company_2).create({
            "move_type": "out_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": self.month_start,
            "is_request_payment": True,
            "company_id": company_2.id,
            "invoice_line_ids": [Command.create({"name": "Fee", "price_unit": 100, "tax_ids": [Command.clear()]})],
        })
        rfp_company_2.write({"approval_state": "approved"})

        payment = self._create_payment(100)

        self.assertNotIn(rfp_company_2, payment.available_rfp_move_ids)

    def test_rfp_stays_draft_until_payment_is_confirmed(self):
        rfp = self._create_rfp(145_200_000)
        self._create_payment(145_200_000, [(rfp, 145_200_000)])

        self.assertEqual(rfp.state, "draft", "Selecting the RFP must not post it yet")
        self.assertFalse(rfp.line_ids.filtered(lambda l: l.parent_state == "posted"))

    # ------------------------------------------------------------------
    # D3 - confirm payment posts and reconciles
    # ------------------------------------------------------------------
    def test_confirm_payment_posts_and_reconciles_rfp(self):
        rfp = self._create_rfp(145_200_000)
        payment = self._create_payment(145_200_000, [(rfp, 145_200_000)], user=self.bank_accountant)

        payment.action_post()

        self.assertEqual(rfp.state, "posted")
        self.assertEqual(rfp.accounting_approval_state, "approved")
        self.assertIn(rfp.payment_state, ("in_payment", "paid"))
        self.assertTrue(self.currency.is_zero(rfp.amount_residual))
        self.assertEqual(rfp.date, payment.date, "MF rule = payment date")

    def test_accounting_date_rules(self):
        payment = self._create_payment(1)
        rfp = self._create_rfp(1, invoice_date=self.month_start)

        self.assertEqual(self.type_payment_date._get_rfp_accounting_date(rfp, payment), payment.date)
        self.assertEqual(self.type_rfp_date._get_rfp_accounting_date(rfp, payment), self.month_start)
        self.assertEqual(
            self.type_period_end._get_rfp_accounting_date(rfp, payment),
            self.month_start + relativedelta(day=31),
        )

    def test_confirm_payment_uses_request_type_date_rule(self):
        rfp_rfp_date = self._create_rfp(100, invoice_type=self.type_rfp_date)
        rfp_period_end = self._create_rfp(200, invoice_type=self.type_period_end)
        payment = self._create_payment(300, [(rfp_rfp_date, 100), (rfp_period_end, 200)])

        payment.action_post()

        self.assertEqual(rfp_rfp_date.date, self.month_start)
        self.assertEqual(rfp_period_end.date, self.month_start + relativedelta(day=31))

    def test_already_posted_rfp_is_reconciled(self):
        rfp = self._create_rfp(500)
        rfp.accounting_approval_state = "approved"
        rfp._post(soft=False)
        payment = self._create_payment(500, [(rfp, 500)])

        payment.action_post()

        self.assertIn(rfp.payment_state, ("in_payment", "paid"))

    def test_last_rfp_partially_paid(self):
        rfp_1 = self._create_rfp(100)
        rfp_2 = self._create_rfp(50)
        payment = self._create_payment(120, [(rfp_1, 100), (rfp_2, 20)])

        payment.action_post()

        self.assertIn(rfp_1.payment_state, ("in_payment", "paid"))
        self.assertEqual(rfp_2.payment_state, "partial")
        self.assertEqual(self.currency.compare_amounts(rfp_2.amount_residual, 30), 0)

    def test_partial_allocation_not_on_last_rfp_is_refused(self):
        rfp_1 = self._create_rfp(100)
        rfp_2 = self._create_rfp(50)
        payment = self._create_payment(150, [(rfp_1, 60), (rfp_2, 50)])

        with self.assertRaises(UserError):
            payment.action_post()
        self.assertEqual(rfp_1.state, "draft")

    def test_allocation_above_payment_amount_is_refused(self):
        rfp_1 = self._create_rfp(100)
        rfp_2 = self._create_rfp(100)
        payment = self._create_payment(150, [(rfp_1, 100), (rfp_2, 100)])

        with self.assertRaises(UserError):
            payment.action_post()

    def test_allocation_above_rfp_amount_is_refused(self):
        rfp = self._create_rfp(100)
        with self.assertRaises(ValidationError):
            self._create_payment(200, [(rfp, 150)])

    def test_unapproved_rfp_cannot_be_posted_from_payment(self):
        rfp = self._create_rfp(100, approved=False)
        payment = self._create_payment(100, [(rfp, 100)])

        with self.assertRaises(UserError):
            payment.action_post()
        self.assertEqual(rfp.state, "draft")

    # ------------------------------------------------------------------
    # D4 - no unpost after e-invoice is published
    # ------------------------------------------------------------------
    def test_reset_to_draft_blocked_when_minvoice_published(self):
        rfp = self._create_rfp(100)
        rfp.accounting_approval_state = "approved"
        rfp._post(soft=False)
        # Simulated publication: no call to the real M-invoice API in tests.
        rfp.minvoice_publish_state = "published"

        with self.assertRaises(UserError):
            rfp.button_draft()
        self.assertEqual(rfp.state, "posted")
        self.assertEqual(rfp.accounting_approval_state, "approved")

    def test_reset_to_draft_allowed_when_minvoice_unpublished(self):
        rfp = self._create_rfp(100)
        rfp.accounting_approval_state = "approved"
        rfp._post(soft=False)

        rfp.button_draft()

        self.assertEqual(rfp.state, "draft")
