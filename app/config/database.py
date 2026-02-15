import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Global singleton MongoDB client and DB instances
client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


async def init_db_client() -> None:
    """Initialize the MongoDB async client and verify connectivity."""
    global client, db

    logger.info("Initializing MongoDB async client")

    try:
        client = AsyncIOMotorClient(settings.MONGO_URL)
        await client.admin.command("ping")
        db = client.get_database(name=settings.MONGO_DB_NAME)
        logger.info("MongoDB client initialized successfully")
    except PyMongoError as e:
        logger.exception("Failed to initialize MongoDB client")
        raise e


async def close_db_client() -> None:
    """Close the MongoDB async client."""
    global client, db
    if client:
        logger.info("Closing MongoDB client")
        client.close()
        client = None
        db = None
        logger.info("MongoDB client closed successfully")
