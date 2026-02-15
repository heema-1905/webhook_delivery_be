from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.dependencies.filtering import WebhookEventFilter
from app.dependencies.pagination import PaginationParams
from app.integrations.redis_client import RedisService
from app.schemas.webhooks import WebhookIngestSchema
from app.utils.constants.webhooks import TASK_LOCKED_SECONDS
from app.utils.enums.webhooks import WebhookStatusEnum
from app.utils.exceptions.webhooks import WebhookEventException


class WebhookEventService:
    """Handles database operations related to storing webhook events."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = self.db.get_collection(name="webhook_events")
        self.redis_service = RedisService()

    async def get_event_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[dict]:
        """Retrieve a webhook event by its idempotency key."""
        event = await self.collection.find_one({"idempotency_key": idempotency_key})
        return event

    async def insert_webhook_event(
        self, webhook_ingest_schema: WebhookIngestSchema
    ) -> dict:
        """Insert a webhook event into the DB, handling idempotency."""
        document = webhook_ingest_schema.model_dump()

        try:
            result = await self.collection.insert_one(document)
            document["_id"] = result.inserted_id
            # If document inserted nto DB then pushing the event to redis queue
            await self.redis_service.left_push_event_to_queue(
                key="webhook:queue", value=str(document["_id"])
            )
            return document
        except DuplicateKeyError:
            existing_event = await self.get_event_by_idempotency_key(
                webhook_ingest_schema.idempotency_key
            )
            if existing_event["data"] != webhook_ingest_schema.data:
                raise WebhookEventException(
                    message="Idempotency key reused with different payload!",
                    error="bad-request",
                )
            return existing_event
        except PyMongoError as exc:
            raise WebhookEventException(message="Database write failed", error=exc)

    async def claim_webhook_event(
        self, current_time: datetime, event_id: ObjectId
    ) -> Optional[dict]:
        """Lock the eligible webhook event for processing."""
        filter_query = {
            "_id": event_id,
            "status": {
                "$in": [
                    WebhookStatusEnum.RECEIVED,
                    WebhookStatusEnum.FAILED_TEMPORARILY,
                ]
            },
            "next_retry_at": {"$lte": current_time},
            "$or": [{"locked_until": None}, {"locked_until": {"$lte": current_time}}],
        }
        update_query = {
            "$set": {
                "locked_until": current_time + timedelta(seconds=TASK_LOCKED_SECONDS)
            }
        }
        event = await self.collection.find_one_and_update(
            filter=filter_query,
            update=update_query,
            sort=[("locked_until", 1), ("received_at", 1)],
            return_document=ReturnDocument.AFTER,
        )
        return event

    async def mark_webhook_event_delivery_status(
        self,
        event_id: ObjectId,
        log_entry: dict,
        status: WebhookStatusEnum,
        next_retry_at: Optional[datetime],
        attempt_count: int,
    ) -> None:
        """Update a webhook's delivery status and append a delivery log."""
        filter_query = {"_id": event_id}
        update_query = {
            "$set": {
                "status": status,
                "locked_until": None,
                "next_retry_at": next_retry_at,
                "attempt_count": attempt_count,
            },
            "$push": {"delivery_logs": log_entry},
        }
        await self.collection.update_one(filter=filter_query, update=update_query)
        return

    async def get_aggregates_by_filtered_dict(self, filter_dict: dict) -> dict:
        """Compute aggregated counts and hourly histogram for filtered events."""
        pipeline = [
            {"$match": filter_dict},
            {
                "$facet": {
                    "count_by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "count_by_event_type": [
                        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
                    ],
                    "hourly_histogram": [
                        {
                            "$group": {
                                "_id": {
                                    "$dateTrunc": {
                                        "date": "$received_at",
                                        "unit": "hour",
                                    }
                                },
                                "count": {"$sum": 1},
                            }
                        },
                        {"$sort": {"_id": 1}},
                    ],
                }
            },
        ]

        agg_cursor = self.collection.aggregate(pipeline)
        agg_result = await agg_cursor.to_list(length=1)
        agg_data = agg_result[0] if agg_result else {}

        for doc in agg_data.get("hourly_histogram", []):
            doc["_id"] = doc["_id"].isoformat()
        return agg_data

    async def get_filtered_search_webhook_events(
        self,
        pagination_params: Optional[PaginationParams] = None,
        filter_params: Optional[WebhookEventFilter] = None,
    ) -> dict:
        """Retrieve filtered webhook events with pagination and aggregates."""
        filter_dict = {}
        if filter_params:
            filter_dict = filter_params._build_filters_dict()
        cursor = self.collection.find(filter_dict)
        if pagination_params:
            total = await self.collection.count_documents(filter=filter_dict)
            pagination_params.total_count = total
            cursor = cursor.skip(pagination_params.offset).limit(
                pagination_params.page_size
            )
        items = await cursor.to_list(
            length=pagination_params.page_size if pagination_params else None
        )
        for item in items:
            if "_id" in item:
                item["_id"] = str(item["_id"])
        agg_data = await self.get_aggregates_by_filtered_dict(filter_dict=filter_dict)

        return {"events": items, "aggregates": agg_data}
