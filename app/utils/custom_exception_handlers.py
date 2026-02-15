import logging

from fastapi import Request, status
from fastapi.exceptions import HTTPException, ResponseValidationError
from fastapi.responses import JSONResponse

from app.utils.constants.core import EXCEPTION_ERROR_CODE_MAP, GENERAL_EXCEPTION_MSG
from app.utils.custom_responses import CustomAPIResponse
from app.utils.error_formatters import ResponseValidationErrorFormatter
from app.utils.exceptions.core import AuthenticationException, UtilsException
from app.utils.exceptions.webhooks import WebhookEventException

logger = logging.getLogger(__name__)


def authentication_exception_handler(
    request: Request, exc: AuthenticationException
) -> JSONResponse:
    """Handles domain-specific authentication exceptions and returns a standardized error response."""
    logger.info(
        f"Authentication exception | {request.method} {request.url.path} | {exc.error}"
    )
    return CustomAPIResponse().get_error_response(
        code=EXCEPTION_ERROR_CODE_MAP.get(exc.error, status.HTTP_401_UNAUTHORIZED),
        message=exc.message,
        errors=exc.error,
    )


def webhook_event_exception_handler(
    request: Request, exc: WebhookEventException
) -> JSONResponse:
    """Handles domain-specific webhook event exceptions and returns a standardized error response."""
    logger.info(
        f"WebhookEvent exception | {request.method} {request.url.path} | {exc.error}"
    )
    return CustomAPIResponse().get_error_response(
        code=EXCEPTION_ERROR_CODE_MAP.get(exc.error, status.HTTP_400_BAD_REQUEST),
        message=exc.message,
        errors=exc.error,
    )


def utils_exception_handler(request: Request, exc: UtilsException) -> JSONResponse:
    """Handles utils exceptions and returns a standardized error response."""
    logger.info(f"Utils exception | {request.method} {request.url.path} | {exc.error}")
    return CustomAPIResponse().get_error_response(
        code=EXCEPTION_ERROR_CODE_MAP.get(
            exc.error, status.HTTP_500_INTERNAL_SERVER_ERROR
        ),
        message=exc.message,
        errors=exc.error,
    )


def response_validation_exception_handler(
    request: Request, exc: ResponseValidationError
) -> JSONResponse:
    """Handles response validation errors and returns a custom API response."""
    logger.error(
        f"Response validation failed | {request.method} {request.url.path}",
        exc_info=True,
    )

    validation_error_dto = ResponseValidationErrorFormatter().format(
        error_list=exc.errors()
    )

    return CustomAPIResponse().get_error_response(
        code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        message=validation_error_dto.message,
        errors=validation_error_dto.errors,
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handles response HTTP exceptions and returns a custom API response."""
    logger.error(
        f"HTTP Exception | {request.method} {request.url.path}: {exc.detail}",
    )

    return CustomAPIResponse().get_error_response(
        code=exc.status_code,
        message=exc.detail,
        headers=(
            exc.headers
            if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            else None
        ),
    )


def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles uncaught exceptions and returns a generic internal server error response."""
    logger.error(
        f"Unhandled exception | {request.method} {request.url.path}",
        exc_info=True,
    )
    return CustomAPIResponse().get_error_response(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=GENERAL_EXCEPTION_MSG,
        errors=str(exc),
    )
