from datetime import datetime, timezone

from fastapi import Header, Request

from app.config.settings import settings
from app.utils.datetime_utils import get_timezone_aware_timestamp_from_string
from app.utils.exceptions.core import AuthenticationException
from app.utils.security.hmac_services import HMACServices


async def verify_webhook_signature(
    request: Request,
    x_signature: str = Header(..., description="HMAC Webhook signature"),
    x_timestamp: str = Header(..., description="Request timestamp"),
) -> bool:
    """Verify webhook authenticity by validating timestamp and HMAC signature."""

    body = await request.body()

    # Verifying timestampy to prevent replay attacks
    request_time = get_timezone_aware_timestamp_from_string(timestamp=x_timestamp)
    current_time = datetime.now(tz=timezone.utc)

    time_difference = abs((current_time - request_time).total_seconds())
    if time_difference > settings.TIMESTAMP_TOLERANCE_SECONDS:
        raise AuthenticationException(
            message="Timestamp too old in request.",
            error="bad-request",
        )

    hmac_services = HMACServices()
    expected_signature = hmac_services.generate_hmac_signature(
        signature_payload=body, x_timestamp=x_timestamp
    )
    if not hmac_services.compare_hmac_signatures(
        received_signature=x_signature, expected_signature=expected_signature
    ):
        raise AuthenticationException(
            message="Invalid HMAC signature",
            error="unauthorized-request",
        )
    return True
