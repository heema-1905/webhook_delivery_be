import hashlib
import hmac

from app.config.settings import settings


class HMACServices:
    """Service for generating and verifying HMAC-SHA256 signatures."""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY.encode()

    def generate_hmac_signature(
        self, signature_payload: bytes, x_timestamp: str
    ) -> str:
        """Generate HMAC-SHA256 signature for payload, including timestamp."""
        # Modifying payload with timestamp for preventing replay attacks
        signature_payload = x_timestamp.encode() + b"." + signature_payload
        signature = hmac.new(
            key=self.secret_key, msg=signature_payload, digestmod=hashlib.sha256
        ).hexdigest()
        return signature

    def compare_hmac_signatures(
        self, received_signature: str, expected_signature: str
    ) -> bool:
        """Securely compare two HMAC signatures."""
        return hmac.compare_digest(received_signature, expected_signature)
