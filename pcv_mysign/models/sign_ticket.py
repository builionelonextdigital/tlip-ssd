from odoo import _, fields, models


class SignTicket(models.Model):
    _inherit = "sign.ticket"

    signing_type = fields.Selection(
        selection_add=[("mysign", "MySign")],
        ondelete={"mysign": "set default"},
    )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_approve(self):
        mysign = self.filtered(lambda r: r.signing_type == "mysign")
        normal = self - mysign

        if normal:
            super(SignTicket, normal).action_approve()

        if not mysign:
            return

        waiting_signers = mysign.mapped("current_signer_id")
        if not waiting_signers:
            return

        return {
            "type": "ir.actions.client",
            "tag": "mysign_popup",
            "target": "new",
            "name": _("MySign Authentication"),
            "context": {"signer_ids": waiting_signers.ids, "footer": False},
        }
