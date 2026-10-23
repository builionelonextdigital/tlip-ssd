import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SignTicketSigner(models.Model):
    _inherit = "sign.ticket.signer"

    state = fields.Selection(
        selection_add=[("waiting_mysign", "Waiting for My Sign")],
        ondelete={"waiting_mysign": "set default"},
    )
    mysign_error = fields.Text(string="MySign Error", readonly=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @api.model
    def _get_waiting_state(self):
        res = super()._get_waiting_state()
        if isinstance(res, str):
            res = [res]

        res.append("waiting_mysign")
        return res

    def _log_mysign_error(self, error: str):
        self.ensure_one()
        self.write({"mysign_error": error, "state": "waiting"})
        _logger.error("MySign signer %d: %s", self.id, error)

    def _build_api_doc(self, doc, target_word):
        """Build a single api_doc dict for one document.

        :param doc: sign.document record.
        :param target_word: Keyword to locate the signature position in the PDF.
        :return: dict ready to be included in MysignAPI.sign_documents payload.
        """
        self.ensure_one()
        file_bytes = doc._get_pdf_bytes()
        line_number = self.line_number
        return {
            "file_bytes": file_bytes,
            "document_id": doc.id,
            "document_name": doc.filename or "",
            "line_number": line_number,
            "coordinate": self.ticket_id.with_context(
                cell_position=line_number
            )._find_keyword_coordinate(target_word, file_bytes),
            "box_spec": self.ticket_id._get_signature_cell_box(),
            "stamp_img": None,
        }

    def _build_api_docs(self, signer):
        """Build the list of api_doc dicts for one signer across all ticket documents.

        :param signer: A single sign.ticket.signer record.
        :return: list of dicts ready to pass to MysignAPI.sign_documents.
        """
        target_word = f"[signer{signer.line_number}]"
        return [
            signer._build_api_doc(doc, target_word)
            for doc in signer.ticket_id.sign_document_ids
        ]

    def _collect_sign_tasks(self):
        """Group signers by MySign account and build all api_docs up front.

        :return: dict {account_id: (account, api_docs, signer_recordset)}
        """
        tasks = {}
        for signer in self:
            account = self.env["mysign.account"]._get_mysign_account(
                signer.user_id, signer.ticket_id.company_id
            )
            if not account:
                raise UserError(
                    _("No MySign account found for user '%s' or company '%s'.")
                    % (signer.user_id.name, signer.ticket_id.company_id.name)
                )
            if account.id not in tasks:
                tasks[account.id] = (account, [], self.browse())
            account_entry, api_docs, signers = tasks[account.id]
            api_docs.extend(self._build_api_docs(signer))
            tasks[account.id] = (account_entry, api_docs, signers | signer)
        return tasks

    def _mysign_postprocess(self, signed_bytes_list, api_docs):
        """Write signed bytes back to documents, update signer status, and transition tickets.

        :param signed_bytes_list: list of bytes returned by MysignAPI.sign_documents.
        :param api_docs: list of api_doc dicts passed to sign_documents (same order).
        """
        for doc_info, signed_bytes in zip(api_docs, signed_bytes_list):
            if not signed_bytes:
                _logger.warning(
                    "MySign: no signed bytes returned for document %s",
                    doc_info.get("document_id"),
                )
                continue
            doc = self.env["sign.document"].browse(doc_info["document_id"])
            doc.write({"file": base64.b64encode(signed_bytes)})

        self.action_sign()
        for ticket in self.mapped("ticket_id"):
            if all(s.state == "signed" for s in ticket.signer_line_ids):
                ticket.write({"state": "approved"})

    def _validate_api_credentials(self, api):
        """Raise UserError if the MySign API credentials are not ready for signing."""
        if not api.credential:
            raise UserError(
                _("No credential available. Please reconnect the MySign account.")
            )
        if not api.credential.is_valid:
            raise UserError(_("MySign credential is not valid. Please reconnect."))
        if not api.credential.certificates:
            raise UserError(
                _("No certificate chain available. Please reconnect the MySign account.")
            )

    def sign_documents(self, account, hash_algo_name="sha256"):
        """Sign all ticket documents for each signer in self using the given MySign account.

        :param account: mysign.account record to use for signing.
        :param hash_algo_name: Hashing algorithm name (default 'sha256').
        """
        account.ensure_one()
        account._ensure_active()
        api = account._get_api()
        self._validate_api_credentials(api)

        api_docs = []
        for signer in self:
            api_docs.extend(self._build_api_docs(signer))

        if not api_docs:
            return

        try:
            signed_bytes_list = api.sign_documents(
                documents=api_docs,
                hash_algo=hash_algo_name,
                description=self[0].ticket_id.name,
            )
        except Exception as e:
            raise UserError(_("Failed to sign documents: %s") % str(e))

        self._mysign_postprocess(signed_bytes_list, api_docs)

    @api.model
    def send_request_to_mysign(self, signer_id):
        signer = self.browse(signer_id)
        if signer.state == "signed":
            raise UserError(_("This document has already been signed."))
        signer.write({"state": "waiting_mysign", "user_id": self.env.user.id, "mysign_error": False})

    def _action_mysign_sign(self):
        tasks = self._collect_sign_tasks()
        for account, api_docs, signers in tasks.values():
            account._ensure_active()
            api = account._get_api()
            signers._validate_api_credentials(api)

            if not api_docs:
                continue

            try:
                signed_bytes_list = api.sign_documents(
                    documents=api_docs,
                    hash_algo="sha256",
                    description=signers[0].ticket_id.name,
                )
            except Exception as e:
                raise UserError(_("Failed to sign documents: %s") % str(e))

            signers._mysign_postprocess(signed_bytes_list, api_docs)
