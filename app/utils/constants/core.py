from fastapi import status

GENERAL_EXCEPTION_MSG: str = "An unexpected error occurred"
EXCEPTION_ERROR_CODE_MAP: dict = {
    "duplicate-entity": status.HTTP_409_CONFLICT,
    "integrity-error": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "resource-not-found": status.HTTP_404_NOT_FOUND,
    "forbid-request": status.HTTP_403_FORBIDDEN,
    "bad-request": status.HTTP_400_BAD_REQUEST,
    "unauthorized-request": status.HTTP_401_UNAUTHORIZED,
    "server-error": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "rate-limited": status.HTTP_429_TOO_MANY_REQUESTS,
    "service-unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
}

RESPONSE_VALIDATION_ERROR_MESSAGE_MAP: dict = {
    "missing": "Required field '{loc}' is missing.",
    "none_required": "Field '{loc}' cannot be null.",
    "extra_forbidden": "Unexpected field '{loc}' found.",
    "enum": "'{msg}' for '{loc}' field.",
}

VALIDATION_ERROR_TYPE_GROUPS: dict = {
    "Invalid data type for '{loc}'.": {
        "int_type",
        "string_type",
        "float_type",
        "bool_type",
    },
    "Invalid structure for '{loc}'.": {
        "list_type",
        "dict_type",
        "model_attributes_type",
    },
    "Missing required field '{loc}'.": {
        "missing",
    },
    "Invalid value for '{loc}'.": {
        "greater_than",
        "greater_than_equal",
        "less_than",
        "less_than_equal",
        "value_error",
        "literal_error",
    },
}
