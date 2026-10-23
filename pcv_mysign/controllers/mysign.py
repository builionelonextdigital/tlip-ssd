import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MySignController(http.Controller):

    @http.route(
        "/mysign/sign",
        type="json",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def sign_signers(self, signer_ids=None, **kwargs):
        """Sign documents for one or more signers in a single API call."""

        if not signer_ids:
            return {"error": "No signer_ids provided"}

        signers = request.env["sign.ticket.signer"].browse(signer_ids)
        invalid = signers.filtered(
            lambda s: not s.exists()
            or s.user_id != request.env.user
            or s.state != "waiting_mysign"
        )
        if invalid:
            return {
                "error": "Some signers not found, not owned by current user, "
                         "or not in waiting_mysign state",
                "invalid_ids": invalid.ids,
            }

        try:
            signers._action_mysign_sign()
        except Exception as exc:
            for signer in signers:
                signer._log_mysign_error(str(exc))
            return {"error": str(exc)}

        return {"ok": True}
