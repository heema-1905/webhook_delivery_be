import asyncio
import logging

from app.config.database import close_db_client, init_db_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize DB, start delivery and retry workers, and handle shutdown."""

    logger.info("Webhook delivery worker startup initiated")

    await init_db_client()
    logger.info("MongoDB initialized successfully for worker")
    from app.tasks.webhook_delivery import (
        webhook_delivery_task,
        webhook_retry_scheduler,
    )

    delivery_task = asyncio.create_task(webhook_delivery_task())
    retry_task = asyncio.create_task(webhook_retry_scheduler())

    try:
        await asyncio.gather(delivery_task, retry_task)

    except Exception:
        logger.exception("Unhandled exception in webhook delivery worker")
        raise

    finally:
        delivery_task.cancel()
        retry_task.cancel()

        await asyncio.gather(delivery_task, retry_task, return_exceptions=True)

        await close_db_client()
        logger.info("MongoDB connection closed for worker")
        logger.info("Webhook delivery worker shutdown completed")


if __name__ == "__main__":
    asyncio.run(main())
