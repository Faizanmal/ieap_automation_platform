"""
Cache Decorator

Provides caching decorators for functions and methods.
"""

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheKey:
    """Cache key builder."""

    prefix: str
    parts: tuple

    def __str__(self) -> str:
        parts_str = ":".join(str(p) for p in self.parts)
        return f"{self.prefix}:{parts_str}"

    @classmethod
    def from_function(
        cls,
        func: Callable,
        args: tuple,
        kwargs: dict,
        prefix: str | None = None
    ) -> "CacheKey":
        """Build cache key from function call."""
        prefix = prefix or f"{func.__module__}.{func.__qualname__}"

        # Build key parts from arguments
        key_parts = []

        for arg in args:
            key_parts.append(cls._hash_value(arg))

        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={cls._hash_value(v)}")

        return cls(prefix=prefix, parts=tuple(key_parts))

    @staticmethod
    def _hash_value(value: Any) -> str:
        """Hash a value for cache key."""
        try:
            serialized = json.dumps(value, sort_keys=True, default=str)
            return hashlib.md5(serialized.encode()).hexdigest()[:12]
        except Exception:
            return str(hash(str(value)))


def cache(
    ttl: int | timedelta = 300,
    prefix: str | None = None,
    key_builder: Callable | None = None,
    condition: Callable | None = None
):
    """
    Caching decorator for async functions.
    
    Args:
        ttl: Time to live in seconds or timedelta
        prefix: Cache key prefix
        key_builder: Custom key builder function
        condition: Function to determine if result should be cached
    
    Usage:
        @cache(ttl=60)
        async def get_user(user_id: str):
            return await db.get(user_id)
    """
    if isinstance(ttl, timedelta):
        ttl_seconds = int(ttl.total_seconds())
    else:
        ttl_seconds = ttl

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from .redis_client import get_redis

            try:
                redis = get_redis()

                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = str(CacheKey.from_function(func, args, kwargs, prefix))

                # Try to get from cache
                cached = await redis.get_json(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached

                logger.debug(f"Cache miss: {cache_key}")

            except Exception as e:
                logger.warning(f"Cache read error: {e}")
                cache_key = None

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if cache_key:
                try:
                    # Check condition
                    should_cache = condition(result) if condition else True

                    if should_cache:
                        await redis.set_json(cache_key, result, ttl=ttl_seconds)
                        logger.debug(f"Cached: {cache_key} (TTL: {ttl_seconds}s)")

                except Exception as e:
                    logger.warning(f"Cache write error: {e}")

            return result

        # Add cache utilities
        wrapper.cache_key_prefix = prefix or f"{func.__module__}.{func.__qualname__}"
        wrapper.invalidate = lambda *args, **kwargs: invalidate_cache(
            str(CacheKey.from_function(func, args, kwargs, prefix))
        )

        return wrapper
    return decorator


def cached_property(ttl: int | timedelta = 300):
    """
    Cached property decorator for class methods.
    
    Usage:
        class User:
            @cached_property(ttl=60)
            async def permissions(self):
                return await self._fetch_permissions()
    """
    if isinstance(ttl, timedelta):
        ttl_seconds = int(ttl.total_seconds())
    else:
        ttl_seconds = ttl

    def decorator(func: Callable):
        attr_name = f"_cached_{func.__name__}"

        @functools.wraps(func)
        async def wrapper(self):
            from .redis_client import get_redis

            try:
                redis = get_redis()

                # Build cache key using object identity
                obj_id = getattr(self, "id", id(self))
                cache_key = f"{self.__class__.__name__}:{obj_id}:{func.__name__}"

                # Try cache
                cached = await redis.get_json(cache_key)
                if cached is not None:
                    return cached

            except Exception as e:
                logger.warning(f"Cache read error: {e}")
                cache_key = None

            # Execute
            result = await func(self)

            # Cache
            if cache_key:
                try:
                    await redis.set_json(cache_key, result, ttl=ttl_seconds)
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")

            return result

        return wrapper
    return decorator


async def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching pattern.
    
    Args:
        pattern: Key pattern to invalidate (supports * wildcard)
    """
    from .redis_client import get_redis

    try:
        redis = get_redis()

        if "*" in pattern:
            # Pattern-based invalidation
            keys = await redis.keys(pattern)
            if keys:
                deleted = await redis.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching: {pattern}")
                return deleted
        else:
            # Direct key invalidation
            deleted = await redis.delete(pattern)
            if deleted:
                logger.info(f"Invalidated cache: {pattern}")
            return deleted

        return 0

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return 0


class CacheManager:
    """
    Cache management utilities.
    """

    def __init__(self):
        self._local_cache = {}

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        from .redis_client import get_redis

        redis = get_redis()
        info = await redis.client.info("memory")

        return {
            "used_memory": info.get("used_memory_human"),
            "used_memory_peak": info.get("used_memory_peak_human"),
            "connected_clients": info.get("connected_clients"),
            "total_keys": await redis.client.dbsize()
        }

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        return await invalidate_cache(f"{namespace}:*")

    async def clear_all(self) -> bool:
        """Clear entire cache (use with caution)."""
        from .redis_client import get_redis

        redis = get_redis()
        await redis.client.flushdb()
        logger.warning("Cache cleared completely")
        return True

    async def warmup(self, keys: list, loader: Callable):
        """Warm up cache with preloaded data."""
        from .redis_client import get_redis

        redis = get_redis()

        for key in keys:
            try:
                if not await redis.exists(key):
                    value = await loader(key)
                    await redis.set_json(key, value)
                    logger.debug(f"Warmed up cache: {key}")
            except Exception as e:
                logger.error(f"Cache warmup error for {key}: {e}")
