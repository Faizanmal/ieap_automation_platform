"""
Rate Limiting Strategies

Different algorithms for rate limiting.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RateLimitState:
    """State for rate limiting"""
    allowed: bool
    remaining: int
    reset_at: float
    retry_after: float | None = None


class RateLimitStrategy(ABC):
    """Abstract base for rate limiting strategies"""

    @abstractmethod
    async def is_allowed(self, key: str, cost: float = 1.0) -> RateLimitState:
        """Check if request is allowed"""

    @abstractmethod
    async def reset(self, key: str):
        """Reset rate limit for key"""


class TokenBucket(RateLimitStrategy):
    """
    Token Bucket Algorithm
    
    Allows bursts of traffic up to bucket size,
    then rate limits to refill rate.
    
    Good for: APIs that need to allow occasional bursts
    """

    def __init__(
        self,
        rate: float,  # Tokens per second
        capacity: int,  # Maximum bucket size
        redis_client = None
    ):
        self.rate = rate
        self.capacity = capacity
        self.redis = redis_client
        self._buckets = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, cost: float = 1.0) -> RateLimitState:
        now = time.time()

        async with self._lock:
            if key not in self._buckets:
                self._buckets[key] = {
                    "tokens": self.capacity,
                    "last_update": now
                }

            bucket = self._buckets[key]

            # Refill tokens based on time elapsed
            elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(
                self.capacity,
                bucket["tokens"] + elapsed * self.rate
            )
            bucket["last_update"] = now

            if bucket["tokens"] >= cost:
                bucket["tokens"] -= cost
                return RateLimitState(
                    allowed=True,
                    remaining=int(bucket["tokens"]),
                    reset_at=now + (self.capacity - bucket["tokens"]) / self.rate
                )
            wait_time = (cost - bucket["tokens"]) / self.rate
            return RateLimitState(
                allowed=False,
                remaining=0,
                reset_at=now + wait_time,
                retry_after=wait_time
            )

    async def reset(self, key: str):
        async with self._lock:
            self._buckets[key] = {
                "tokens": self.capacity,
                "last_update": time.time()
            }


class SlidingWindow(RateLimitStrategy):
    """
    Sliding Window Algorithm
    
    Tracks requests in a sliding time window.
    More accurate than fixed window, prevents burst at window edges.
    
    Good for: Most general rate limiting needs
    """

    def __init__(
        self,
        limit: int,
        window_size: int,  # Seconds
        redis_client = None
    ):
        self.limit = limit
        self.window_size = window_size
        self.redis = redis_client
        self._windows = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, cost: float = 1.0) -> RateLimitState:
        now = time.time()
        window_start = now - self.window_size

        async with self._lock:
            if key not in self._windows:
                self._windows[key] = []

            # Remove expired entries
            self._windows[key] = [
                (ts, c) for ts, c in self._windows[key] if ts > window_start
            ]

            # Calculate current usage
            current_usage = sum(c for _, c in self._windows[key])

            if current_usage + cost <= self.limit:
                self._windows[key].append((now, cost))
                return RateLimitState(
                    allowed=True,
                    remaining=int(self.limit - current_usage - cost),
                    reset_at=now + self.window_size
                )
            # Find when oldest request will expire
            if self._windows[key]:
                oldest = min(ts for ts, _ in self._windows[key])
                retry_after = oldest + self.window_size - now
            else:
                retry_after = 0

            return RateLimitState(
                allowed=False,
                remaining=0,
                reset_at=now + self.window_size,
                retry_after=max(0, retry_after)
            )

    async def reset(self, key: str):
        async with self._lock:
            self._windows[key] = []


class FixedWindow(RateLimitStrategy):
    """
    Fixed Window Algorithm
    
    Simple counter that resets at fixed intervals.
    Simple but can allow 2x burst at window edges.
    
    Good for: Simple, high-performance rate limiting
    """

    def __init__(
        self,
        limit: int,
        window_size: int,  # Seconds
        redis_client = None
    ):
        self.limit = limit
        self.window_size = window_size
        self.redis = redis_client
        self._counters = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, cost: float = 1.0) -> RateLimitState:
        now = time.time()
        window_key = int(now / self.window_size)
        full_key = f"{key}:{window_key}"

        async with self._lock:
            if full_key not in self._counters:
                self._counters[full_key] = 0

            if self._counters[full_key] + cost <= self.limit:
                self._counters[full_key] += cost
                return RateLimitState(
                    allowed=True,
                    remaining=int(self.limit - self._counters[full_key]),
                    reset_at=(window_key + 1) * self.window_size
                )
            return RateLimitState(
                allowed=False,
                remaining=0,
                reset_at=(window_key + 1) * self.window_size,
                retry_after=(window_key + 1) * self.window_size - now
            )

    async def reset(self, key: str):
        now = time.time()
        window_key = int(now / self.window_size)
        full_key = f"{key}:{window_key}"

        async with self._lock:
            self._counters[full_key] = 0


class LeakyBucket(RateLimitStrategy):
    """
    Leaky Bucket Algorithm
    
    Processes requests at a constant rate.
    Excess requests are queued (up to capacity).
    
    Good for: Smoothing traffic, queue-based processing
    """

    def __init__(
        self,
        rate: float,  # Requests per second to process
        capacity: int,  # Maximum queue size
        redis_client = None
    ):
        self.rate = rate
        self.capacity = capacity
        self.redis = redis_client
        self._queues = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str, cost: float = 1.0) -> RateLimitState:
        now = time.time()

        async with self._lock:
            if key not in self._queues:
                self._queues[key] = {
                    "water_level": 0,
                    "last_leak": now
                }

            queue = self._queues[key]

            # Leak water based on time elapsed
            elapsed = now - queue["last_leak"]
            leaked = elapsed * self.rate
            queue["water_level"] = max(0, queue["water_level"] - leaked)
            queue["last_leak"] = now

            if queue["water_level"] + cost <= self.capacity:
                queue["water_level"] += cost

                # Calculate when this request will be "processed"
                process_time = queue["water_level"] / self.rate

                return RateLimitState(
                    allowed=True,
                    remaining=int(self.capacity - queue["water_level"]),
                    reset_at=now + process_time
                )
            # Queue is full
            return RateLimitState(
                allowed=False,
                remaining=0,
                reset_at=now + queue["water_level"] / self.rate,
                retry_after=(queue["water_level"] + cost - self.capacity) / self.rate
            )

    async def reset(self, key: str):
        async with self._lock:
            self._queues[key] = {
                "water_level": 0,
                "last_leak": time.time()
            }
