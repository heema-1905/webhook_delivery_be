from datetime import datetime
from typing import Optional

from fastapi import Query

from app.utils.enums.webhooks import WebhookStatusEnum
from app.utils.exceptions.core import UtilsException


class WebhookEventFilter:
    """Filter and validate webhook query parameters."""

    def __init__(
        self,
        status: Optional[WebhookStatusEnum] = Query(
            None, description="Webhook event status filter"
        ),
        timestamp_from: Optional[datetime] = Query(
            None, description="Time range filter"
        ),
        timestamp_to: Optional[datetime] = Query(None, description="Time range filter"),
        event_type: Optional[str] = Query(None, description="Event type filter"),
    ):
        self.status = status
        self.timestamp_from = timestamp_from
        self.timestamp_to = timestamp_to
        self.event_type = event_type

    def validate_timestamp(self):
        """Ensure start timestamp is before end timestamp."""
        if self.timestamp_from and self.timestamp_to:
            if self.timestamp_from >= self.timestamp_to:
                raise UtilsException(
                    message="Timestamp start should always be less than timestamp end!",
                    error="bad-request",
                )

    def _build_filters_dict(self) -> dict:
        """Build a MongoDB-compatible filters dictionary."""
        filters_dict = {}
        if self.status:
            filters_dict["status"] = self.status
        if self.event_type:
            filters_dict["event_type"] = self.event_type
        if self.timestamp_from or self.timestamp_to:
            filters_dict["received_at"] = {}
            if self.timestamp_from:
                filters_dict["received_at"]["$gte"] = self.timestamp_from
            if self.timestamp_to:
                filters_dict["received_at"]["$lte"] = self.timestamp_to
        return filters_dict
