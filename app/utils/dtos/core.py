from typing import List, NamedTuple


class CorsAllowedSettingsDTO(NamedTuple):
    """Holds parsed CORS configuration values for origins, headers, and methods."""

    allowed_origins: List[str]
    allowed_headers: List[str]
    allowed_methods: List[str]


class ValidationErrorDTO(NamedTuple):
    """Represents a structured validation error with message and field-level details."""

    message: str
    errors: dict
