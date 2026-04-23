"""
Redis Client

Enterprise Redis client with connection pooling and async support.
"""

import json
import logging
from datetime import timedelta
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client with connection pooling.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        max_connections: int = 50,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        decode_responses: bool = True
    ):
        self.url = url
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.decode_responses = decode_responses

        self._pool: ConnectionPool | None = None
        self._client: aioredis.Redis | None = None

    async def connect(self):
        """Initialize Redis connection pool."""
        logger.info("Connecting to Redis...")

        self._pool = aioredis.ConnectionPool.from_url(
            self.url,
            max_connections=self.max_connections,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=self.retry_on_timeout,
            decode_responses=self.decode_responses
        )

        self._client = aioredis.Redis(connection_pool=self._pool)

        # Test connection
        await self._client.ping()
        logger.info("Redis connection established")

    async def disconnect(self):
        """Close Redis connection."""
        logger.info("Disconnecting from Redis...")

        if self._client:
            await self._client.close()

        if self._pool:
            await self._pool.disconnect()

        logger.info("Redis connection closed")

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    # String operations
    async def get(self, key: str) -> str | None:
        """Get value by key."""
        return await self._client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | timedelta | None = None
    ) -> bool:
        """Set key-value with optional TTL."""
        if ttl:
            return await self._client.setex(key, ttl, value)
        return await self._client.set(key, value)

    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        return await self._client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        return await self._client.exists(*keys)

    # JSON operations
    async def get_json(self, key: str) -> Any | None:
        """Get and parse JSON value."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: int | timedelta | None = None
    ) -> bool:
        """Set JSON value."""
        return await self.set(key, json.dumps(value), ttl)

    # Hash operations
    async def hget(self, name: str, key: str) -> str | None:
        """Get hash field value."""
        return await self._client.hget(name, key)

    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field value."""
        return await self._client.hset(name, key, value)

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields."""
        return await self._client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        return await self._client.hdel(name, *keys)

    # List operations
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to list head."""
        return await self._client.lpush(key, *values)

    async def rpush(self, key: str, *values: str) -> int:
        """Push values to list tail."""
        return await self._client.rpush(key, *values)

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """Get list range."""
        return await self._client.lrange(key, start, stop)

    async def llen(self, key: str) -> int:
        """Get list length."""
        return await self._client.llen(key)

    # Set operations
    async def sadd(self, key: str, *values: str) -> int:
        """Add values to set."""
        return await self._client.sadd(key, *values)

    async def smembers(self, key: str) -> set:
        """Get all set members."""
        return await self._client.smembers(key)

    async def sismember(self, key: str, value: str) -> bool:
        """Check if value is in set."""
        return await self._client.sismember(key, value)

    # Sorted set operations
    async def zadd(
        self,
        key: str,
        mapping: dict[str, float],
        nx: bool = False,
        xx: bool = False
    ) -> int:
        """Add values to sorted set."""
        return await self._client.zadd(key, mapping, nx=nx, xx=xx)

    async def zrange(
        self,
        key: str,
        start: int,
        stop: int,
        withscores: bool = False
    ) -> list:
        """Get sorted set range."""
        return await self._client.zrange(key, start, stop, withscores=withscores)

    async def zrank(self, key: str, value: str) -> int | None:
        """Get rank of value in sorted set."""
        return await self._client.zrank(key, value)

    # Counter operations
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        return await self._client.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        return await self._client.decrby(key, amount)

    # TTL operations
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration."""
        return await self._client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get key TTL."""
        return await self._client.ttl(key)

    # Pattern operations
    async def keys(self, pattern: str) -> list[str]:
        """Get keys matching pattern."""
        return await self._client.keys(pattern)

    async def scan_iter(self, match: str = "*", count: int = 100):
        """Iterate over keys matching pattern."""
        async for key in self._client.scan_iter(match=match, count=count):
            yield key

    # Pub/Sub operations
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel."""
        return await self._client.publish(channel, message)

    def pubsub(self):
        """Get pub/sub client."""
        return self._client.pubsub()

    # Lock operations
    def lock(
        self,
        name: str,
        timeout: float | None = None,
        blocking_timeout: float | None = None
    ):
        """Get distributed lock."""
        return self._client.lock(name, timeout=timeout, blocking_timeout=blocking_timeout)

    # Pipeline operations
    def pipeline(self, transaction: bool = True):
        """Get pipeline for batch operations."""
        return self._client.pipeline(transaction=transaction)

    @property
    def client(self) -> aioredis.Redis:
        """Get underlying Redis client."""
        return self._client


# Global Redis instance
_redis: RedisClient | None = None


def get_redis() -> RedisClient:
    """Get global Redis client."""
    global _redis
    if _redis is None:
        from config import get_settings
        settings = get_settings()
        _redis = RedisClient(
            url=settings.cache.redis_url,
            max_connections=settings.cache.max_connections
        )
    return _redis


async def init_redis():
    """Initialize Redis connection."""
    redis = get_redis()
    await redis.connect()


async def close_redis():
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.disconnect()
        _redis = None
