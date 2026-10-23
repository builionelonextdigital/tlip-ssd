class MysignCredential:
    """Parsed representation of a MySign credentials/info response."""

    def __init__(self, data: dict):
        cert = data.get("cert", {})
        key = data.get("key", {})

        # Certificate info
        self.cert_status = cert.get("status", "")
        self.issuer_dn = cert.get("issuerDN", "")
        self.subject_dn = cert.get("subjectDN", "")
        self.serial_number = cert.get("serialNumber", "")
        self.valid_from = cert.get("validFrom", "")
        self.valid_to = cert.get("validTo", "")
        self.certificates = cert.get("certificates", [])   # list of base64 DER strings

        # Key info
        self.key_status = key.get("status", "")
        self.key_algorithms = key.get("algo", [])
        self.key_length = key.get("len", 0)
        self.key_curve = key.get("curve")

        # Credential metadata
        self.credential_id = data.get("credential_id", "")
        self.description = data.get("description", "")
        self.auth_mode = data.get("authMode", "")
        self.multisign = data.get("multisign", 1)
        self.scal = data.get("SCAL", "")
        self.phone_number = data.get("phone_number", "")
        self.subscriber_id = data.get("subscriber_id", "")
        self.sign_package = data.get("sign_package", "")

    @property
    def is_valid(self):
        return self.cert_status == "valid" and self.key_status == "enabled"

    @property
    def end_entity_cert_b64(self):
        """Base64 DER string of the end-entity certificate (first in chain)."""
        return self.certificates[0] if self.certificates else None

    def __repr__(self):
        return (
            f"<MysignCredential id={self.credential_id!r} "
            f"subject={self.subject_dn!r} valid={self.is_valid}>"
        )
