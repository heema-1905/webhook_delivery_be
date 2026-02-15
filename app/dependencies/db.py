import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import database

logger = logging.getLogger(__name__)


def get_db() -> AsyncIOMotorDatabase:
    """Return the initialized MongoDB database instance or raise error if unavailable."""
    if database.db is None:
        logger.critical("Mongodb instance not initialized.")
        raise RuntimeError("Mongodb instance not initialized.")
    return database.db
