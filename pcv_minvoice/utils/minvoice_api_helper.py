import requests
import json
from datetime import datetime, timezone, timedelta
import logging

from ..const import MINVOICE_TOKEN_EXPIRE_HOURS

_logger = logging.getLogger(__name__)


class NoValidTokenException(Exception):
    pass

class MInvoiceAPIError(Exception):
    pass


class MInvoiceAPI:
    def __init__(self, credential):
        self.username = credential.username
        self.password = credential.password
        self.production_host = credential.production_host
        self.access_token = None
        self.expires_at = datetime.now(timezone.utc)

    @property
    def _current_token(self):
        if self.access_token and self.expires_at and self.expires_at > datetime.now(timezone.utc):
            return self.access_token
        else:
            raise NoValidTokenException()
        
    def _get_url(self, endpoint):
        return f"{self.production_host}{endpoint}"

    def _get_access_token(self):
        return self._renew_access_token_if_necessary()

    def _renew_access_token_if_necessary(self):
        try:
            return self._current_token
        except Exception:
            return self.renew_access_token()

    def renew_access_token(self):
        token_info = self.refresh_access_token()
        self.access_token = token_info["token"]
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=MINVOICE_TOKEN_EXPIRE_HOURS)
        return self._current_token

    def refresh_access_token(self):
        result = self.connect_with_credential()
        return result.json()
    
    def _send_request(self, method: str, endpoint: str, raw_response: bool = False, **kwargs):
        try:
            headers = self.get_headers_with_token(**kwargs.pop("headers", {}))
            response = requests.request(
                method=method,
                url=self._get_url(endpoint),
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            if raw_response:
                return {
                    "ok": True,
                    "data": response.content
                }
            
            result = response.json()
            return  {
                "ok": result.get('code') == '00',
                "data": result,
            }
        except requests.exceptions.HTTPError as e:
            message = f"HTTP error occurred: {str(e)}"
            _logger.error(message)
            return self._error_notification(message)
        except Exception as e:
            message = f"Failed to send request to M-Invoice: {str(e)}"
            _logger.error(message)
            return self._error_notification(message)
    
    def _error_notification(self, message: str):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "danger",
                "title": "Thông báo!",
                "message": message,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def get_headers(self, **kwargs):
        headers = {"Content-Type": "application/json", **kwargs}
        return headers

    def get_headers_with_token(self, **kwargs):
        headers = {
            "Content-Type": "application/json",
            'Authorization': 'Bearer %s' % self._get_access_token(),
            **kwargs,
        }
        return headers

    def _authenticate_with_credential(self, credential):
        try:
            response = requests.post(
                url=self._get_url("/api/Account/Login"), headers=self.get_headers(), data=json.dumps(credential)
            )
            return response
        except Exception as e:
            message = f"Failed when try to send request to M-Invoice: {str(e)}"
            _logger.error(message)
            return {
                "error": True,
                "message": message
            }

    def make_request(self, method: str, endpoint: str, **kwargs):
        return self._send_request(method, endpoint, **kwargs)

    def _get_credential_dict(self):
        return {
            "username": self.username,
            "password": self.password,
        }

    def connect_with_credential(self):
        credential = self._get_credential_dict()
        return self._authenticate_with_credential(credential)
