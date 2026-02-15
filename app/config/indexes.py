from app.dependencies.db import get_db


class CreateDbCollectionIndexes:

    def __init__(self):
        self.db = get_db()

    async def create_webhook_events_index(self):
        """Createing required MongoDB indexes for specific collection by retrieving it."""
        collection = self.db.get_collection(name="webhook_events")
        await collection.create_index(
            "idempotency_key",
            unique=True,
        )

        await collection.create_index(
            [
                ("status", 1),
                ("next_retry_at", 1),
                ("locked_until", 1),
                ("received_at", 1),
            ]
        )

    async def create_all_collections_indexes(self):
        """Create required MongoDB indexes for all collections."""
        await self.create_webhook_events_index()
