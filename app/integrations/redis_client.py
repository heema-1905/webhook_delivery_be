from typing import Any

from redis.asyncio import Redis

from app.config.settings import settings


class RedisService:
    """
    Servie class defining utility methods for interacting with redis along with initializing with redis
    client
    """

    def __init__(self):
        self.redis_client = Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0
        )

    async def left_push_event_to_queue(self, key: str, value: str):
        """Pushes an event to the left of the Redis queue."""
        await self.redis_client.lpush(key, value)

    async def brpop_event_from_queue(self, key: str):
        """Blocks and pops an event from the Redis queue."""
        return await self.redis_client.brpop(keys=key)

    async def brpoplpush_event_from_queue(self, source: str, destination: str):
        """Atomically moves event from queue to processing list."""
        return await self.redis_client.brpoplpush(source, destination)

    async def zadd_event_to_queue(self, name: str, mapping: Any):
        """Adds an event to a Redis sorted set with a score."""
        await self.redis_client.zadd(name=name, mapping=mapping)

    async def get_events_by_zrangescore(self, key: str, now: int, min: int = 0):
        """Fetches events from the Redis sorted set by range."""
        return await self.redis_client.zrangebyscore(name=key, min=min, max=now)

    async def remove_event_from_zset(self, key: str, value: str):
        """Removes an event from the Redis sorted set."""
        await self.redis_client.zrem(key, value)
