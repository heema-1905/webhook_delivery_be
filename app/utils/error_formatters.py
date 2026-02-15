from abc import ABC, abstractmethod
from typing import Any, List, Optional, Sequence, Tuple

from app.utils.constants.core import (
    RESPONSE_VALIDATION_ERROR_MESSAGE_MAP,
    VALIDATION_ERROR_TYPE_GROUPS,
)
from app.utils.dtos.core import ValidationErrorDTO


class ValidationErrorFormatter(ABC):
    """Validation error formatter contract."""

    @abstractmethod
    def format(self, error_list: Sequence[Any]) -> ValidationErrorDTO:
        """Formats validation errors into a structured DTO."""
        pass


class BaseValidationErrorFormatter(ValidationErrorFormatter):
    """Shared validation error formatting logic."""

    message_template_map: dict

    def _get_error_message_template(self, error_type: str) -> Optional[str]:
        """Resolves the message template for a given validation error type."""
        message_template = self.message_template_map.get(error_type)
        if not message_template:
            for template, type_group in VALIDATION_ERROR_TYPE_GROUPS.items():
                if error_type in type_group:
                    message_template = template
        return message_template

    def _format_message_template(
        self, error: dict, message_template: str, error_type: str
    ) -> Tuple[str, str]:
        """Formats a validation error message and extracts its field location."""
        loc = error.get("loc", [""])[-1]
        msg = error.get("msg", "")
        if error_type == "value_error":
            message = message_template.format(msg=msg.replace("Value error, ", ""))
        elif error_type == "enum":
            message = message_template.format(loc=loc, msg=msg)
        elif error_type == "json_invalid":
            message = message_template
        else:
            message = message_template.format(loc=loc)
        return message, loc

    def format(self, error_list: Sequence[Any]) -> ValidationErrorDTO:
        """Formats validation errors into a structured DTO."""
        messages: List[str] = []
        error_map: dict = {}
        for error in error_list:
            error_type: str = error.get("type")
            message_template = self._get_error_message_template(error_type=error_type)
            if message_template:
                message, loc = self._format_message_template(
                    error=error,
                    message_template=message_template,
                    error_type=error_type,
                )
                messages.append(message)
                if error_type == "json_invalid":
                    error_map["body"] = "Malformed JSON or invalid structure"
                    error_map["type"] = "bad-request"
                else:
                    error_map[loc] = message
        return ValidationErrorDTO(message=" ".join(set(messages)), errors=error_map)


class ResponseValidationErrorFormatter(BaseValidationErrorFormatter):
    """Formats response validation errors."""

    message_template_map = RESPONSE_VALIDATION_ERROR_MESSAGE_MAP
