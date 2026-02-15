from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import (
    BaseAggregateSchema,
    BasePaginatedResponseSchema,
    BaseResponseSchema,
)
from app.utils.enums.webhooks import WebhookStatusEnum


class WebhookBaseSchema(BaseModel):
    """Base schema for webhook data with metadata and delivery info."""

    data: Any
    idempotency_key: str
    status: WebhookStatusEnum = WebhookStatusEnum.RECEIVED
    received_at: datetime = datetime.now(tz=timezone.utc)
    event_type: Optional[str] = None
    attempt_count: int = 0
    delivery_logs: List[dict] = []
    locked_until: Optional[datetime] = None
    next_retry_at: Optional[datetime] = datetime.now(tz=timezone.utc)


class WebhookIngestSchema(WebhookBaseSchema):
    """Schema class defining fields required while ingesting webhook data to db"""

    pass


class WebhookDeliveryLogsSchema(BaseModel):
    """Schema representing a single webhook delivery attempt log."""

    timestamp: datetime
    attempt_number: int
    status_code: int
    success: bool


class WebhookReadSchema(WebhookBaseSchema):
    """Schema for reading webhook data including delivery logs."""

    id: str = Field(..., alias="_id")
    delivery_logs: List[WebhookDeliveryLogsSchema]

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class WebhookAggregateSchema(BaseModel):
    """Schema for aggregated counts of webhook events."""

    count_by_status: List[BaseAggregateSchema]
    count_by_event_type: List[BaseAggregateSchema]
    hourly_histogram: List[BaseAggregateSchema]


class WebhookSearchAggregateSchema(BaseModel):
    """Schema for search results combining events and aggregates."""

    events: List[WebhookReadSchema]
    aggregates: WebhookAggregateSchema


class WebhookListPaginatedSchema(BasePaginatedResponseSchema):
    """Paginated schema for a list of webhook search results."""

    results: WebhookSearchAggregateSchema


class WebhookListResponseSchema(BaseResponseSchema):
    """Response schema for webhook list API endpoint."""

    data: WebhookListPaginatedSchema
