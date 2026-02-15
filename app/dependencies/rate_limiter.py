import time

from fastapi import status
from fastapi.exceptions import HTTPException
from redis.exceptions import ConnectionError, ResponseError

from app.integrations.redis_client import RedisService
from app.utils.exceptions.core import UtilsException


class TokenBucketRateLimiter:
    """Rate limiter using a token bucket algorithm backed by Redis."""

    def __init__(self, rate: int, capacity: int):
        self.redis_client = RedisService().redis_client
        self.rate = rate  # Requests allowed per second
        self.capacity = capacity  # Max burst capacity of bucket

        with open(file="app/scripts/token_bucket.lua", mode="r") as rl_file:
            self._script = self.redis_client.register_script(script=rl_file.read())

    async def is_request_allowed(self, key: str, requested_tokens: float = 1) -> bool:
        """Check if a request can proceed under current rate limits."""
        try:
            now = time.time()

            result = await self._script(
                keys=[key],
                args=[self.rate, self.capacity, requested_tokens, now],
            )
            return bool(result)
        except ConnectionError:
            raise UtilsException(
                message="Rate limiting service unavailable due to connection error",
                error="service-unavailable",
            )
        except ResponseError as exc:
            raise UtilsException(message="Error reading script.", error=str(exc))


class RateLimiterDependency:
    """FastAPI dependency wrapper for token bucket rate limiting."""

    def __init__(self, limiter: TokenBucketRateLimiter, key: str):
        """Initialize dependency with a limiter instance and key."""
        self.limiter = limiter
        self.key = key

    async def __call__(self):
        """Enforce rate limit and raise 429 if exceeded."""
        request_allowed = await self.limiter.is_request_allowed(key=self.key)

        if not request_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests! Please try again after some time.",
                headers={"Retry-After": "5"},
            )
