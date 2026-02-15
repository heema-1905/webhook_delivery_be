from fastapi import status

from app.schemas.base import BaseResponseSchema
from app.schemas.webhooks import WebhookListResponseSchema

WEBHOOK_INGEST_RESPONSES: dict = {
    status.HTTP_201_CREATED: {
        "model": BaseResponseSchema,
        "description": "Webhook ingested successfully",
    },
    status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Unauthorized request due to signature mismatch"
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
}

WEBHOOK_DOWNSTREAM_RECEIVE_RESPONSES: dict = {
    status.HTTP_201_CREATED: {
        "model": BaseResponseSchema,
        "description": "Webhook received successfully",
    },
    status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
    status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Request rate limited"},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
}

WEBHOOK_SEARCH_RESPONSES: dict = {
    status.HTTP_201_CREATED: {
        "model": WebhookListResponseSchema,
        "description": "Webhook events retrieved successfully!",
    },
    status.HTTP_400_BAD_REQUEST: {"description": "Invalid request"},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
}
