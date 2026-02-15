import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx
from bson import ObjectId
from fastapi import status

from app.config.settings import settings
from app.dependencies.db import get_db
from app.integrations.redis_client import RedisService
from app.services.webhooks import WebhookEventService
from app.utils.constants.webhooks import (
    DELIVERY_TIMEOUT,
    DOWNSTREAM_URL,
    EXPONENTIAL_BACKOFF,
    MAX_RETRY_ATTEMPTS,
)
from app.utils.enums.webhooks import WebhookStatusEnum

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

http_client = httpx.AsyncClient(timeout=DELIVERY_TIMEOUT)
redis_service = RedisService()
webhook_event_service = WebhookEventService(db=get_db())


async def process_webhook_event_delivery(event: dict):
    """Process a single webhook delivery attempt with info logs."""
    event_id = event["_id"]
    attempt_count = event["attempt_count"] + 1
    now = datetime.now(tz=timezone.utc)

    status_code = None
    retry_delay = None
    final_status = None
    success = False
    response = None

    logger.info(f"[Webhook {event_id}] Starting delivery attempt {attempt_count}")

    try:
        response = await http_client.post(
            url=DOWNSTREAM_URL,
            json=event["data"],
        )
        status_code = response.status_code
        success = 200 <= status_code < 300
        logger.info(f"[Webhook {event_id}] Received response {status_code}")
    except httpx.TimeoutException:
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
        logger.info(f"[Webhook {event_id}] Timeout occurred")
    except Exception as exc:
        logger.exception(f"[Webhook {event_id}] Unexpected error: {exc}")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if success:
        final_status = WebhookStatusEnum.DELIVERED
        logger.info(f"[Webhook {event_id}] Delivery succeeded")
    else:
        if attempt_count >= MAX_RETRY_ATTEMPTS:
            final_status = WebhookStatusEnum.FAILED_PERMANENTLY
            logger.info(
                f"[Webhook {event_id}] Max attempts reached, marking permanently failed"
            )
        else:
            if status_code == 429 or (500 <= status_code < 600):
                retry_after = (
                    response.headers.get("Retry-After")
                    if response and status_code == 429
                    else None
                )
                retry_delay = (
                    int(retry_after)
                    if retry_after
                    else EXPONENTIAL_BACKOFF[attempt_count - 1]
                )
                final_status = WebhookStatusEnum.FAILED_TEMPORARILY
                logger.info(
                    f"[Webhook {event_id}] Temporary failure, will retry in {retry_delay}s"
                )
            else:
                final_status = WebhookStatusEnum.FAILED_PERMANENTLY
                logger.info(f"[Webhook {event_id}] Permanent failure, not retrying")

    next_retry_at = (
        now + timedelta(seconds=retry_delay)
        if final_status == WebhookStatusEnum.FAILED_TEMPORARILY
        else None
    )

    log_entry = {
        "timestamp": now,
        "attempt_number": attempt_count,
        "status_code": status_code,
        "success": final_status == WebhookStatusEnum.DELIVERED,
    }

    await webhook_event_service.mark_webhook_event_delivery_status(
        event_id=event_id,
        log_entry=log_entry,
        status=final_status,
        next_retry_at=next_retry_at,
        attempt_count=attempt_count,
    )
    if final_status == WebhookStatusEnum.FAILED_TEMPORARILY:
        retry_timestamp = int(next_retry_at.timestamp())

        await redis_service.zadd_event_to_queue(
            name="webhook:retry", mapping={str(event_id): retry_timestamp}
        )
    logger.info(
        f"[Webhook {event_id}] Delivery attempt {attempt_count} processed with final status {final_status}"
    )


async def webhook_retry_scheduler():
    """Continuously moves due retry events from Redis ZSET back to the main queue."""
    while True:
        now = int(datetime.now(timezone.utc).timestamp())
        # Fetching ready retries
        ready_events = await redis_service.get_events_by_zrangescore(
            key="webhook:retry",
            now=now,
        )
        if ready_events:
            for event_id in ready_events:
                # Moving back to main queue
                await redis_service.left_push_event_to_queue(
                    key="webhook:queue",
                    value=event_id,
                )

                # Remove from retry set
                await redis_service.remove_event_from_zset(
                    key="webhook:retry",
                    value=event_id,
                )

        await asyncio.sleep(1)


async def webhook_delivery_task():
    """Main task that polls and processes webhook events with graceful shutdown."""
    semaphore = asyncio.Semaphore(value=settings.CONCURRENT_WORKERS)
    tasks = set()

    async def worker(event: dict):
        try:
            async with semaphore:
                await process_webhook_event_delivery(event)
        except asyncio.CancelledError:
            logger.info(f"Worker for event {event['_id']} cancelled during shutdown.")
            raise
        except Exception as e:
            logger.exception(
                f"Unexpected error in worker for event {event['_id']}: {e}"
            )

    try:
        while True:
            _, event_id = await redis_service.brpop_event_from_queue(
                key="webhook:queue"
            )
            if isinstance(event_id, bytes):
                event_id = event_id.decode()
            event = await webhook_event_service.claim_webhook_event(
                current_time=datetime.now(tz=timezone.utc), event_id=ObjectId(event_id)
            )
            if not event:
                continue
            task = asyncio.create_task(worker(event))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
    except asyncio.CancelledError:
        logger.info("Webhook delivery main loop cancelled. Shutting down...")
    finally:
        if tasks:
            logger.info(f"Waiting for {len(tasks)} running delivery tasks to finish...")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        # Closing global HTTP client on shutdown
        await http_client.aclose()
        logger.info("Webhook delivery task shutdown complete.")
