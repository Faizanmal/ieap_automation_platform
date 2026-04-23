"""
Bulkhead Pattern

Limits concurrent access to a resource to prevent overload.
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class BulkheadFullError(Exception):
    """Exception raised when bulkhead is at capacity"""

    def __init__(self, name: str, max_concurrent: int, queue_size: int):
        self.name = name
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        super().__init__(
            f"Bulkhead '{name}' is full (max_concurrent={max_concurrent}, queue_size={queue_size})"
        )


@dataclass
class BulkheadStats:
    """Bulkhead statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    rejected_requests: int = 0
    current_concurrent: int = 0
    current_queued: int = 0
    max_concurrent_seen: int = 0
    max_queue_seen: int = 0
    total_wait_time_ms: float = 0.0


class Bulkhead:
    """
    Bulkhead pattern implementation for limiting concurrent access.
    
    Features:
    - Limit concurrent executions
    - Optional waiting queue with timeout
    - Sync and async support
    - Metrics and monitoring
    
    Usage:
        bulkhead = Bulkhead(name="db-pool", max_concurrent=10, max_queue=5)
        
        @bulkhead
        async def query_database():
            # Limited to 10 concurrent calls
            pass
        
        # Or as context manager
        async with bulkhead:
            await query_database()
    """

    def __init__(
        self,
        name: str,
        max_concurrent: int = 10,
        max_queue: int = 0,
        queue_timeout: float = 30.0
    ):
        """
        Initialize bulkhead.
        
        Args:
            name: Bulkhead name for identification
            max_concurrent: Maximum concurrent executions
            max_queue: Maximum size of waiting queue (0 = no queue)
            queue_timeout: Maximum time to wait in queue (seconds)
        """
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_queue = max_queue
        self.queue_timeout = queue_timeout

        # Async semaphore
        self._async_semaphore = asyncio.Semaphore(max_concurrent)

        # Sync semaphore
        self._sync_semaphore = threading.Semaphore(max_concurrent)

        # Stats
        self._stats = BulkheadStats()
        self._lock = threading.Lock()

        # Queue tracking
        self._queued = 0
        self._queue_lock = asyncio.Lock()

    @property
    def stats(self) -> BulkheadStats:
        """Get bulkhead statistics"""
        return self._stats

    def _update_stats(self, acquired: bool = False, released: bool = False, rejected: bool = False):
        """Update bulkhead stats"""
        with self._lock:
            self._stats.total_requests += 1 if acquired or rejected else 0

            if acquired:
                self._stats.current_concurrent += 1
                self._stats.max_concurrent_seen = max(
                    self._stats.max_concurrent_seen,
                    self._stats.current_concurrent
                )

            if released:
                self._stats.current_concurrent -= 1
                self._stats.successful_requests += 1

            if rejected:
                self._stats.rejected_requests += 1

    async def acquire(self) -> bool:
        """Acquire a slot (async)"""
        start_time = time.time()

        # Check if we can queue
        async with self._queue_lock:
            if self._async_semaphore.locked():
                if self.max_queue > 0 and self._queued < self.max_queue:
                    self._queued += 1
                    self._stats.current_queued = self._queued
                    self._stats.max_queue_seen = max(
                        self._stats.max_queue_seen,
                        self._queued
                    )
                elif self.max_queue == 0 or self._queued >= self.max_queue:
                    self._update_stats(rejected=True)
                    raise BulkheadFullError(self.name, self.max_concurrent, self.max_queue)

        try:
            # Try to acquire with timeout
            await asyncio.wait_for(
                self._async_semaphore.acquire(),
                timeout=self.queue_timeout
            )

            # Record wait time
            wait_time = (time.time() - start_time) * 1000
            self._stats.total_wait_time_ms += wait_time

            self._update_stats(acquired=True)
            return True

        except TimeoutError:
            self._update_stats(rejected=True)
            raise BulkheadFullError(self.name, self.max_concurrent, self.max_queue)

        finally:
            async with self._queue_lock:
                if self._queued > 0:
                    self._queued -= 1
                    self._stats.current_queued = self._queued

    def release(self):
        """Release a slot"""
        self._async_semaphore.release()
        self._update_stats(released=True)

    def acquire_sync(self) -> bool:
        """Acquire a slot (sync)"""
        if self._sync_semaphore.acquire(blocking=True, timeout=self.queue_timeout):
            self._update_stats(acquired=True)
            return True

        self._update_stats(rejected=True)
        raise BulkheadFullError(self.name, self.max_concurrent, self.max_queue)

    def release_sync(self):
        """Release a slot (sync)"""
        self._sync_semaphore.release()
        self._update_stats(released=True)

    def __call__(self, func: Callable) -> Callable:
        """Decorator for sync/async functions"""
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                await self.acquire()
                try:
                    return await func(*args, **kwargs)
                finally:
                    self.release()
            return async_wrapper
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            self.acquire_sync()
            try:
                return func(*args, **kwargs)
            finally:
                self.release_sync()
        return sync_wrapper

    async def __aenter__(self):
        """Async context manager entry"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.release()
        return False

    def __enter__(self):
        """Sync context manager entry"""
        self.acquire_sync()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit"""
        self.release_sync()
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize bulkhead state"""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "max_queue": self.max_queue,
            "stats": {
                "total_requests": self._stats.total_requests,
                "successful_requests": self._stats.successful_requests,
                "rejected_requests": self._stats.rejected_requests,
                "current_concurrent": self._stats.current_concurrent,
                "current_queued": self._stats.current_queued,
                "max_concurrent_seen": self._stats.max_concurrent_seen,
                "avg_wait_time_ms": (
                    self._stats.total_wait_time_ms / max(1, self._stats.successful_requests)
                )
            }
        }


class BulkheadRegistry:
    """Registry for managing multiple bulkheads"""

    _instance = None
    _bulkheads: dict[str, Bulkhead] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._bulkheads = {}
        return cls._instance

    @classmethod
    def get_or_create(cls, name: str, **kwargs) -> Bulkhead:
        """Get existing or create new bulkhead"""
        if name not in cls._bulkheads:
            cls._bulkheads[name] = Bulkhead(name=name, **kwargs)
        return cls._bulkheads[name]

    @classmethod
    def get(cls, name: str) -> Bulkhead | None:
        """Get bulkhead by name"""
        return cls._bulkheads.get(name)

    @classmethod
    def all(cls) -> dict[str, Bulkhead]:
        """Get all bulkheads"""
        return cls._bulkheads.copy()


def bulkhead(
    name: str,
    max_concurrent: int = 10,
    max_queue: int = 0,
    **kwargs
) -> Callable:
    """
    Decorator to add bulkhead to a function.
    
    Usage:
        @bulkhead("database", max_concurrent=20)
        async def query_db():
            pass
    """
    bh = BulkheadRegistry.get_or_create(name, max_concurrent=max_concurrent, max_queue=max_queue, **kwargs)
    return bh
