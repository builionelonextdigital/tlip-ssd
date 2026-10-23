import asyncio
import base64
import logging
import requests
import random

from datetime import datetime
from typing import Optional
from pyhanko.sign.signers.csc_signer import (
    CSCServiceSessionInfo,
    _process_certificate_info_response,
)

from .common import BASE_CSC_SERVICE, BASE_URL_VTSS
from .mysign_credential import MysignCredential
from .document_sign_helper import (
    prepare_sig_field_spec,
    prepare_sig_meta,
    prepare_stamp_style,
    sign_pdf_async,
)

_logger = logging.getLogger(__name__)


class NoValidTokenException(Exception):
    pass


class MysignAPIError(Exception):
    pass


class MysignAPI:
    def __init__(self, config, account):
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.profile_id = config.profile_id
        self.user_id = account.code
        self.url_api = config.url_api
        self.tsa_url = config.tsa_url
        self._access_token = account.access_token if account else None
        self._token_expiry = account.token_expiry if account else None
        self.credential_id = None
        self.credential_info = {}
        self.credential: MysignCredential | None = None
        self._load_credentials()

    def _load_credentials(self):
        try:
            status_code, data = self.get_credentials_list(
                certificates="none", cert_info=False, auth_info=False
            )
            if status_code != 200:
                _logger.warning("MysignAPI: credentials/list returned %s", status_code)
                return
            credential_ids = data.get("credentialIDs", [])
            if not credential_ids:
                _logger.warning(
                    "MysignAPI: no credentialIDs in credentials/list response"
                )
                return
            self.credential_id = credential_ids[0]

            status_code, info = self.get_credential_info(self.credential_id)
            if status_code != 200:
                _logger.warning("MysignAPI: credential_info returned %s", status_code)
                return
            self.credential_info = info
            self.credential = MysignCredential(info)
        except Exception:
            _logger.warning(
                "MysignAPI: failed to load credentials on init", exc_info=True
            )

    @property
    def _current_token(self):
        if self._access_token and (
            not self._token_expiry or self._token_expiry > datetime.now()
        ):
            return self._access_token
        raise NoValidTokenException("No valid access token available.")

    def _get_login_url(self):
        return f"{self.url_api.rstrip('/')}/login"

    def _get_url_vtss(self, endpoint):
        return f"{BASE_URL_VTSS}{endpoint}"

    def _get_headers(self, authenticated: bool = True, **extra):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **extra,
        }
        if authenticated:
            headers["Authorization"] = f"Bearer {self._current_token}"
        return headers

    def _send_request(self, method, url, authenticated=True, **kwargs):
        try:
            headers = self._get_headers(authenticated, **kwargs.pop("headers", {}))
            response = requests.request(
                method=method, url=url, headers=headers, **kwargs
            )
            return response.status_code, response.json()
        except NoValidTokenException:
            raise
        except Exception as e:
            _logger.error("MySign API request failed [%s %s]: %s", method, url, str(e))
            raise MysignAPIError(str(e))

    def _build_csc_context(self):
        """Return (credential_info, session_info, signer_name) shared across sign tasks."""
        credential_info = _process_certificate_info_response(self.credential_info)
        session_info = CSCServiceSessionInfo(
            service_url=BASE_CSC_SERVICE,
            credential_id=self.credential_id,
            oauth_token=self._access_token,
        )
        return (
            credential_info,
            session_info,
            self.credential.subject_dn if self.credential else "Unknown Signer",
        )

    def _encode_b64_text(self, text: str) -> str:
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")

    async def _sign_doc(
        self,
        doc,
        session_info,
        credential_info,
        signer_cert_name,
        hash_algo,
        encoded_description,
    ):
        doc_entry = {}
        if doc.get("document_id") is not None:
            doc_entry["document_id"] = doc["document_id"]
        if doc.get("document_name"):
            doc_entry["document_name"] = self._encode_b64_text(doc["document_name"])

        signer_name = doc.get("signer_name") or signer_cert_name

        field_name = f"signature_{doc.get('line_number', '1')}_{doc.get('document_id', '1')}_{random.randint(1000, 9999)}"
        stamp_style, img_width, composite_height = prepare_stamp_style(
            signer_name=signer_name,
            dn=signer_cert_name,
            stamp_img=doc.get("stamp_img"),
        )
        sig_meta = prepare_sig_meta(
            field_name=field_name,
            hash_algo=hash_algo,
            signer_name=signer_name,
        )
        sig_field_spec = prepare_sig_field_spec(
            field_name=field_name, coordinate=doc.get("coordinate"),
            box_spec=doc.get("box_spec"), img_width=img_width, composite_height=composite_height,
        )

        return await sign_pdf_async(
            file_bytes=doc["file_bytes"],
            session_info=session_info,
            credential_info=credential_info,
            stamp_style=stamp_style,
            sig_meta=sig_meta,
            sig_field_spec=sig_field_spec,
            tsa_url=self.tsa_url,
            documents=[doc_entry] if doc_entry else None,
            description=encoded_description,
        )

    def login(self, user_id=None):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "profile_id": self.profile_id,
            "user_id": user_id or self.user_id,
        }
        return self._send_request(
            "POST", self._get_login_url(), authenticated=False, json=payload
        )

    def get_credentials_list(
        self, certificates="chain", cert_info=True, auth_info=True
    ):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "certificates": certificates,
            "certInfo": cert_info,
            "authInfo": auth_info,
        }
        return self._send_request(
            "POST", self._get_url_vtss("/credentials/list"), json=payload
        )

    def get_credential_info(
        self, credential_id, certificates="chain", cert_info=True, auth_info=True
    ):
        payload = {
            "credentialID": credential_id,
            "certificates": certificates,
            "certInfo": cert_info,
            "authInfo": auth_info,
        }
        return self._send_request(
            "POST", self._get_url_vtss("/credentials/info"), json=payload
        )

    def sign_documents(
        self,
        documents: list,
        hash_algo: str = "sha256",
        description: Optional[str] = None,
    ) -> list:
        """Sign multiple PDFs concurrently. Returns list of signed bytes in the same order."""
        credential_info, session_info, signer_name = self._build_csc_context()
        encoded_description = (
            self._encode_b64_text(description) if description else None
        )

        async def _run_all():
            for result in await asyncio.gather(
                *[
                    self._sign_doc(
                        doc,
                        session_info,
                        credential_info,
                        signer_name,
                        hash_algo,
                        encoded_description,
                    )
                    for doc in documents
                ]
            ):
                yield result

        async def _collect_all():
            return [result async for result in _run_all()]

        return asyncio.run(_collect_all())
