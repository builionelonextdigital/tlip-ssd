# ----------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------

BASE_HOST = "https://remotesigning.viettel.vn"
BASE_URL = f"{BASE_HOST}/vtss/service/ras/v1"
BASE_URL_VTSS = f"{BASE_HOST}/vtss/service/ras/csc/v1"
# Base service URL for CSCServiceSessionInfo — endpoint_url() appends /csc/v1/<endpoint>
BASE_CSC_SERVICE = f"{BASE_HOST}/vtss/service/ras"

# ----------------------------------------------------------
# Hash Algorithm OIDs
# ----------------------------------------------------------

HASH_ALGO_MAP = {
    "sha256": "2.16.840.1.101.3.4.2.1",
    "sha384": "2.16.840.1.101.3.4.2.2",
    "sha512": "2.16.840.1.101.3.4.2.3",
}


def get_hash_algo_oid(name: str) -> str:
    return HASH_ALGO_MAP.get(name.lower())

# ----------------------------------------------------------
# Error Codes
# ----------------------------------------------------------

CODE_ERROR = [
    ("58071", "The request is missing a required parameter, includes an invalid parameter value, includes a parameter more than once, or is otherwise malformed."),
    ("59033", "Failed to process request - user ID or password is invalid."),
]


def get_error_description(code: str) -> str:
    for error_code, description in CODE_ERROR:
        if error_code == str(code):
            return description
    return ""

# ----------------------------------------------------------
# UI Helpers
# ----------------------------------------------------------


def show_notification(title: str, message: str, notif_type: str = "success") -> dict:
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "title": title,
            "message": message,
            "type": notif_type,
        },
    }
