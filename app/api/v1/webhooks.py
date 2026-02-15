from fastapi import APIRouter, Body, Depends, Header, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.openapi_schemas.webhooks import (
    WEBHOOK_DOWNSTREAM_RECEIVE_RESPONSES,
    WEBHOOK_INGEST_RESPONSES,
    WEBHOOK_SEARCH_RESPONSES,
)
from app.dependencies.auth import verify_webhook_signature
from app.dependencies.db import get_db
from app.dependencies.filtering import WebhookEventFilter
from app.dependencies.pagination import PaginationParams
from app.dependencies.rate_limiter import RateLimiterDependency, TokenBucketRateLimiter
from app.schemas.base import BaseResponseSchema
from app.schemas.webhooks import (
    WebhookIngestSchema,
    WebhookListPaginatedSchema,
    WebhookListResponseSchema,
)
from app.services.webhooks import WebhookEventService
from app.utils.custom_responses import CustomAPIResponse

webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@webhook_router.post(
    path="/ingest",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponseSchema,
    responses=WEBHOOK_INGEST_RESPONSES,
)
async def ingest_webhook(
    payload: dict = Body(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    _: bool = Depends(verify_webhook_signature),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Ingest and persist validated webhook payload."""

    webhook_event_service = WebhookEventService(db=db)
    webhook_ingest_schema = WebhookIngestSchema(
        data=payload,
        event_type=payload.get("event_type"),
        idempotency_key=idempotency_key,
    )
    result = await webhook_event_service.insert_webhook_event(
        webhook_ingest_schema=webhook_ingest_schema
    )
    return CustomAPIResponse().get_success_response(
        code=status.HTTP_201_CREATED,
        message="Webhook ingested successfully!",
        data={"id": str(result["_id"])},
    )


downstream_rate_limiter = TokenBucketRateLimiter(rate=3, capacity=3)


@webhook_router.post(
    path="/downstream/receive",
    status_code=status.HTTP_200_OK,
    response_model=BaseResponseSchema,
    responses=WEBHOOK_DOWNSTREAM_RECEIVE_RESPONSES,
)
async def downstream_webhook_receive(
    _: None = Depends(
        RateLimiterDependency(
            limiter=downstream_rate_limiter, key="rate_limit:downstream"
        )
    )
) -> dict:
    """Accept webhook calls from downstream services."""
    # import asyncio

    # await asyncio.sleep(3)
    # NOTE: Adding sleep time here for the purpose of testing the httpx timeout error.
    return CustomAPIResponse().get_success_response(
        code=status.HTTP_200_OK, message="Webhook received successfully!"
    )


@webhook_router.get(
    path="/search",
    status_code=status.HTTP_200_OK,
    response_model=WebhookListResponseSchema,
    responses=WEBHOOK_SEARCH_RESPONSES,
)
async def list_webhook_events(
    pagination_params: PaginationParams = Depends(),
    filter_params: WebhookEventFilter = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Retrieve paginated webhook events based on filters."""
    filter_params.validate_timestamp()
    webhook_event_service = WebhookEventService(db=db)
    webhook_events = await webhook_event_service.get_filtered_search_webhook_events(
        pagination_params=pagination_params, filter_params=filter_params
    )
    return CustomAPIResponse().get_success_response(
        code=status.HTTP_200_OK,
        message="Webhook events retrieved successfully!",
        data=WebhookListPaginatedSchema(
            total_count=pagination_params.total_count, results=webhook_events
        ),
    )
