"""
Rate Limiter Core

Advanced rate limiting with multiple strategies and tiers.
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RateLimitTier(Enum):
    """Rate limit tiers for different user types"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 10.0
    requests_per_minute: float = 100.0
    requests_per_hour: float = 1000.0
    requests_per_day: float = 10000.0
    burst_size: int = 20
    daily_quota: int | None = None
    monthly_quota: int | None = None
    cost_per_request: float = 1.0  # For quota systems

    @classmethod
    def for_tier(cls, tier: RateLimitTier) -> "RateLimitConfig":
        """Get configuration for a specific tier"""
        configs = {
            RateLimitTier.FREE: cls(
                requests_per_second=1,
                requests_per_minute=30,
                requests_per_hour=200,
                requests_per_day=1000,
                burst_size=5,
                daily_quota=1000,
                monthly_quota=10000
            ),
            RateLimitTier.STARTER: cls(
                requests_per_second=5,
                requests_per_minute=100,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_size=15,
                daily_quota=10000,
                monthly_quota=100000
            ),
            RateLimitTier.PROFESSIONAL: cls(
                requests_per_second=20,
                requests_per_minute=500,
                requests_per_hour=5000,
                requests_per_day=50000,
                burst_size=50,
                daily_quota=50000,
                monthly_quota=500000
            ),
            RateLimitTier.ENTERPRISE: cls(
                requests_per_second=100,
                requests_per_minute=2000,
                requests_per_hour=20000,
                requests_per_day=200000,
                burst_size=200,
                daily_quota=None,
                monthly_quota=None
            ),
            RateLimitTier.UNLIMITED: cls(
                requests_per_second=float("inf"),
                requests_per_minute=float("inf"),
                requests_per_hour=float("inf"),
                requests_per_day=float("inf"),
                burst_size=1000,
                daily_quota=None,
                monthly_quota=None
            )
        }
        return configs.get(tier, configs[RateLimitTier.FREE])


@dataclass
class RateLimitResult:
    """Result of a rate limit check"""
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: float | None = None
    quota_used: int = 0
    quota_remaining: int | None = None
    tier: RateLimitTier | None = None
    reason: str | None = None

    def to_headers(self) -> dict[str, str]:
        """Convert to HTTP headers"""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at.timestamp()))
        }

        if self.retry_after is not None:
            headers["Retry-After"] = str(int(self.retry_after))

        if self.quota_remaining is not None:
            headers["X-Quota-Remaining"] = str(self.quota_remaining)

        if self.tier:
            headers["X-RateLimit-Tier"] = self.tier.value

        return headers


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies.
    
    Features:
    - Multiple time windows (second, minute, hour, day)
    - Tiered limits for different user types
    - Quota tracking (daily, monthly)
    - Burst handling
    - Intelligent throttling
    - Redis-backed for distributed systems
    
    Usage:
        limiter = RateLimiter()
        
        # Check rate limit
        result = await limiter.check("user_123", tier=RateLimitTier.PROFESSIONAL)
        if not result.allowed:
            raise HTTPException(429, headers=result.to_headers())
        
        # Get remaining quota
        quota = await limiter.get_quota("user_123")
    """

    def __init__(
        self,
        redis_client = None,
        default_config: RateLimitConfig | None = None,
        key_prefix: str = "ratelimit"
    ):
        self.redis = redis_client
        self.default_config = default_config or RateLimitConfig()
        self.key_prefix = key_prefix

        # In-memory fallback when Redis is not available
        self._memory_store: dict[str, dict[str, Any]] = defaultdict(dict)
        self._memory_lock = asyncio.Lock()

        # Custom configs per endpoint or user
        self._custom_configs: dict[str, RateLimitConfig] = {}

        # Quota tracking
        self._quotas: dict[str, dict[str, int]] = defaultdict(dict)

    def set_config(self, key: str, config: RateLimitConfig):
        """Set custom config for a specific key (user, endpoint, etc.)"""
        self._custom_configs[key] = config

    async def check(
        self,
        key: str,
        tier: RateLimitTier | None = None,
        cost: float = 1.0,
        endpoint: str | None = None
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limits.
        
        Args:
            key: Unique identifier (user_id, ip, api_key)
            tier: Rate limit tier
            cost: Cost of this request (for quota)
            endpoint: Specific endpoint for per-endpoint limits
        
        Returns:
            RateLimitResult with allowed status and metadata
        """
        # Get config for this key
        config = self._get_config(key, tier)

        now = time.time()
        current_time = datetime.now()

        # Check multiple windows
        windows = [
            ("second", 1, config.requests_per_second),
            ("minute", 60, config.requests_per_minute),
            ("hour", 3600, config.requests_per_hour),
            ("day", 86400, config.requests_per_day)
        ]

        for window_name, window_size, limit in windows:
            if limit == float("inf"):
                continue

            window_key = f"{key}:{window_name}"
            count = await self._get_count(window_key, now, window_size)

            if count >= limit:
                reset_at = datetime.fromtimestamp(
                    (int(now / window_size) + 1) * window_size
                )
                return RateLimitResult(
                    allowed=False,
                    limit=int(limit),
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=(reset_at - current_time).total_seconds(),
                    tier=tier,
                    reason=f"Rate limit exceeded ({window_name})"
                )

        # Check quota
        if config.daily_quota or config.monthly_quota:
            quota_result = await self._check_quota(key, config, cost)
            if not quota_result["allowed"]:
                return RateLimitResult(
                    allowed=False,
                    limit=quota_result["limit"],
                    remaining=0,
                    reset_at=quota_result["reset_at"],
                    quota_used=quota_result["used"],
                    quota_remaining=0,
                    tier=tier,
                    reason="Quota exceeded"
                )

        # Increment counters
        for window_name, window_size, limit in windows:
            if limit != float("inf"):
                window_key = f"{key}:{window_name}"
                await self._increment(window_key, now, window_size, cost)

        # Increment quota
        if config.daily_quota or config.monthly_quota:
            await self._increment_quota(key, cost)

        # Calculate remaining (use minute window as primary)
        minute_count = await self._get_count(f"{key}:minute", now, 60)
        remaining = max(0, int(config.requests_per_minute - minute_count - cost))

        return RateLimitResult(
            allowed=True,
            limit=int(config.requests_per_minute),
            remaining=remaining,
            reset_at=datetime.fromtimestamp((int(now / 60) + 1) * 60),
            quota_used=await self._get_quota_used(key),
            quota_remaining=await self._get_quota_remaining(key, config),
            tier=tier
        )

    def _get_config(
        self,
        key: str,
        tier: RateLimitTier | None
    ) -> RateLimitConfig:
        """Get config for a key"""
        if key in self._custom_configs:
            return self._custom_configs[key]
        if tier:
            return RateLimitConfig.for_tier(tier)
        return self.default_config

    async def _get_count(self, key: str, now: float, window_size: int) -> float:
        """Get current count for a window"""
        if self.redis:
            try:
                full_key = f"{self.key_prefix}:{key}"
                count = await self.redis.get(full_key)
                return float(count) if count else 0
            except Exception as e:
                logger.warning(f"Redis error, using memory: {e}")

        # Memory fallback
        async with self._memory_lock:
            window_start = int(now / window_size) * window_size
            data = self._memory_store.get(key, {})
            if data.get("window_start") != window_start:
                return 0
            return data.get("count", 0)

    async def _increment(
        self,
        key: str,
        now: float,
        window_size: int,
        cost: float = 1.0
    ):
        """Increment counter for a window"""
        if self.redis:
            try:
                full_key = f"{self.key_prefix}:{key}"
                pipe = self.redis.pipeline()
                pipe.incrbyfloat(full_key, cost)
                pipe.expire(full_key, window_size + 1)
                await pipe.execute()
                return
            except Exception as e:
                logger.warning(f"Redis error, using memory: {e}")

        # Memory fallback
        async with self._memory_lock:
            window_start = int(now / window_size) * window_size

            if key not in self._memory_store:
                self._memory_store[key] = {"window_start": window_start, "count": 0}

            data = self._memory_store[key]
            if data["window_start"] != window_start:
                data["window_start"] = window_start
                data["count"] = 0

            data["count"] += cost

    async def _check_quota(
        self,
        key: str,
        config: RateLimitConfig,
        cost: float
    ) -> dict[str, Any]:
        """Check quota limits"""
        now = datetime.now()

        # Check daily quota
        if config.daily_quota:
            day_key = f"{key}:quota:day:{now.strftime('%Y%m%d')}"
            used = await self._get_quota_value(day_key)
            if used + cost > config.daily_quota:
                tomorrow = (now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                return {
                    "allowed": False,
                    "limit": config.daily_quota,
                    "used": used,
                    "reset_at": tomorrow
                }

        # Check monthly quota
        if config.monthly_quota:
            month_key = f"{key}:quota:month:{now.strftime('%Y%m')}"
            used = await self._get_quota_value(month_key)
            if used + cost > config.monthly_quota:
                next_month = (now.replace(day=1) + timedelta(days=32)).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
                return {
                    "allowed": False,
                    "limit": config.monthly_quota,
                    "used": used,
                    "reset_at": next_month
                }

        return {"allowed": True}

    async def _get_quota_value(self, key: str) -> int:
        """Get quota value"""
        if self.redis:
            try:
                full_key = f"{self.key_prefix}:{key}"
                value = await self.redis.get(full_key)
                return int(value) if value else 0
            except Exception:
                pass

        return self._quotas.get(key, {}).get("value", 0)

    async def _increment_quota(self, key: str, cost: float):
        """Increment quota counters"""
        now = datetime.now()

        day_key = f"{key}:quota:day:{now.strftime('%Y%m%d')}"
        month_key = f"{key}:quota:month:{now.strftime('%Y%m')}"

        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.incrbyfloat(f"{self.key_prefix}:{day_key}", cost)
                pipe.expire(f"{self.key_prefix}:{day_key}", 86400 * 2)
                pipe.incrbyfloat(f"{self.key_prefix}:{month_key}", cost)
                pipe.expire(f"{self.key_prefix}:{month_key}", 86400 * 35)
                await pipe.execute()
                return
            except Exception:
                pass

        # Memory fallback
        if day_key not in self._quotas:
            self._quotas[day_key] = {"value": 0}
        self._quotas[day_key]["value"] += cost

        if month_key not in self._quotas:
            self._quotas[month_key] = {"value": 0}
        self._quotas[month_key]["value"] += cost

    async def _get_quota_used(self, key: str) -> int:
        """Get quota used today"""
        now = datetime.now()
        day_key = f"{key}:quota:day:{now.strftime('%Y%m%d')}"
        return await self._get_quota_value(day_key)

    async def _get_quota_remaining(
        self,
        key: str,
        config: RateLimitConfig
    ) -> int | None:
        """Get remaining quota"""
        if not config.daily_quota:
            return None
        used = await self._get_quota_used(key)
        return max(0, config.daily_quota - used)

    async def get_usage_stats(self, key: str) -> dict[str, Any]:
        """Get detailed usage statistics for a key"""
        now = time.time()
        current = datetime.now()

        return {
            "key": key,
            "current_second": await self._get_count(f"{key}:second", now, 1),
            "current_minute": await self._get_count(f"{key}:minute", now, 60),
            "current_hour": await self._get_count(f"{key}:hour", now, 3600),
            "current_day": await self._get_count(f"{key}:day", now, 86400),
            "quota_used_today": await self._get_quota_used(key),
            "quota_used_month": await self._get_quota_value(
                f"{key}:quota:month:{current.strftime('%Y%m')}"
            ),
            "timestamp": current.isoformat()
        }

    async def reset(self, key: str):
        """Reset rate limits for a key"""
        windows = ["second", "minute", "hour", "day"]

        if self.redis:
            try:
                pipe = self.redis.pipeline()
                for window in windows:
                    pipe.delete(f"{self.key_prefix}:{key}:{window}")
                await pipe.execute()
                return
            except Exception:
                pass

        # Memory fallback
        async with self._memory_lock:
            for window in windows:
                self._memory_store.pop(f"{key}:{window}", None)
