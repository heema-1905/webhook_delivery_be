from datetime import datetime, timezone

from app.utils.exceptions.core import UtilsException


def get_timezone_aware_timestamp_from_string(timestamp: str) -> datetime:
    """Parses an ISO 8601 timestamp string and returns a UTC timezone-aware datetime object."""
    try:
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            raise UtilsException(
                message="Timestamp must include timezone.",
                error="bad-request",
            )
        return dt.astimezone(tz=timezone.utc)
    except ValueError:
        raise UtilsException(
            message="Invalid imestamp format! Must be ISO 8601.", error="bad-request"
        )
