"""
Circuit Breaker Pattern

Prevents cascading failures by failing fast when a service is unhealthy.
"""

import asyncio
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation, requests go through
    OPEN = "open"          # Failure threshold exceeded, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitStats:
    """Circuit breaker statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0

    def record_success(self):
        self.total_requests += 1
        self.successful_requests += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.now()

    def record_failure(self):
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.now()

    def record_rejected(self):
        self.total_requests += 1
        self.rejected_requests += 1

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests


class CircuitBreakerError(Exception):
    """Exception raised when circuit is open"""

    def __init__(self, circuit_name: str, state: CircuitState, retry_after: float | None = None):
        self.circuit_name = circuit_name
        self.state = state
        self.retry_after = retry_after
        super().__init__(f"Circuit '{circuit_name}' is {state.value}")


class CircuitBreaker:
    """
    Circuit Breaker implementation.
    
    Usage:
        breaker = CircuitBreaker(
            name="external-api",
            failure_threshold=5,
            recovery_timeout=30,
            half_open_max_calls=3
        )
        
        @breaker
        async def call_external_api():
            # API call that might fail
            pass
        
        # Or use directly
        async with breaker:
            result = await call_external_api()
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        excluded_exceptions: tuple | None = None,
        on_open: Callable | None = None,
        on_close: Callable | None = None,
        on_half_open: Callable | None = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name for identification
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again (half-open)
            half_open_max_calls: Max calls allowed in half-open state
            success_threshold: Successes needed in half-open to close circuit
            excluded_exceptions: Exceptions that don't count as failures
            on_open: Callback when circuit opens
            on_close: Callback when circuit closes
            on_half_open: Callback when circuit goes half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions or ()

        # Callbacks
        self._on_open = on_open
        self._on_close = on_close
        self._on_half_open = on_half_open

        # State
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_state_change = datetime.now()
        self._half_open_calls = 0
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._transition_to(CircuitState.HALF_OPEN)
            return self._state

    @property
    def stats(self) -> CircuitStats:
        """Get circuit statistics"""
        return self._stats

    def _should_attempt_recovery(self) -> bool:
        """Check if we should attempt recovery"""
        time_since_open = (datetime.now() - self._last_state_change).total_seconds()
        return time_since_open >= self.recovery_timeout

    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state"""
        old_state = self._state
        self._state = new_state
        self._last_state_change = datetime.now()

        logger.info(f"Circuit '{self.name}' transitioned from {old_state.value} to {new_state.value}")

        if new_state == CircuitState.OPEN and self._on_open:
            try:
                self._on_open(self)
            except Exception as e:
                logger.error(f"Error in on_open callback: {e}")
        elif new_state == CircuitState.CLOSED and self._on_close:
            try:
                self._on_close(self)
            except Exception as e:
                logger.error(f"Error in on_close callback: {e}")
        elif new_state == CircuitState.HALF_OPEN and self._on_half_open:
            self._half_open_calls = 0
            try:
                self._on_half_open(self)
            except Exception as e:
                logger.error(f"Error in on_half_open callback: {e}")

    def _record_success(self):
        """Record a successful call"""
        with self._lock:
            self._stats.record_success()

            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    def _record_failure(self, exception: Exception):
        """Record a failed call"""
        with self._lock:
            # Check if exception should be excluded
            if isinstance(exception, self.excluded_exceptions):
                return

            self._stats.record_failure()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._stats.consecutive_failures >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def _allow_request(self) -> bool:
        """Check if a request should be allowed"""
        current_state = self.state  # This triggers state transition check

        with self._lock:
            if current_state == CircuitState.CLOSED:
                return True
            if current_state == CircuitState.OPEN:
                self._stats.record_rejected()
                return False
            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                self._stats.record_rejected()
                return False

        return False

    def __call__(self, func: Callable) -> Callable:
        """Decorator for sync/async functions"""
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self:
                    return await func(*args, **kwargs)
            return async_wrapper
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not self._allow_request():
                retry_after = self.recovery_timeout - (datetime.now() - self._last_state_change).total_seconds()
                raise CircuitBreakerError(self.name, self._state, max(0, retry_after))

            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except Exception as e:
                self._record_failure(e)
                raise
        return sync_wrapper

    async def __aenter__(self):
        """Async context manager entry"""
        if not self._allow_request():
            retry_after = self.recovery_timeout - (datetime.now() - self._last_state_change).total_seconds()
            raise CircuitBreakerError(self.name, self._state, max(0, retry_after))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_val is None:
            self._record_success()
        else:
            self._record_failure(exc_val)
        return False

    def __enter__(self):
        """Sync context manager entry"""
        if not self._allow_request():
            retry_after = self.recovery_timeout - (datetime.now() - self._last_state_change).total_seconds()
            raise CircuitBreakerError(self.name, self._state, max(0, retry_after))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit"""
        if exc_val is None:
            self._record_success()
        else:
            self._record_failure(exc_val)
        return False

    def reset(self):
        """Reset the circuit breaker"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._stats = CircuitStats()
            self._last_state_change = datetime.now()
            self._half_open_calls = 0

        logger.info(f"Circuit '{self.name}' reset")

    def force_open(self):
        """Force the circuit to open"""
        with self._lock:
            self._transition_to(CircuitState.OPEN)

    def force_close(self):
        """Force the circuit to close"""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)

    def to_dict(self) -> dict[str, Any]:
        """Serialize circuit breaker state"""
        return {
            "name": self.name,
            "state": self._state.value,
            "stats": {
                "total_requests": self._stats.total_requests,
                "successful_requests": self._stats.successful_requests,
                "failed_requests": self._stats.failed_requests,
                "rejected_requests": self._stats.rejected_requests,
                "failure_rate": self._stats.failure_rate,
                "consecutive_failures": self._stats.consecutive_failures,
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
                "half_open_max_calls": self.half_open_max_calls,
            }
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    _instance = None
    _breakers: dict[str, CircuitBreaker] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._breakers = {}
        return cls._instance

    @classmethod
    def get_or_create(
        cls,
        name: str,
        **kwargs
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name=name, **kwargs)
        return cls._breakers[name]

    @classmethod
    def get(cls, name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name"""
        return cls._breakers.get(name)

    @classmethod
    def all(cls) -> dict[str, CircuitBreaker]:
        """Get all circuit breakers"""
        return cls._breakers.copy()

    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers"""
        for breaker in cls._breakers.values():
            breaker.reset()


# Convenience function
def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    **kwargs
) -> Callable:
    """
    Decorator to add circuit breaker to a function.
    
    Usage:
        @circuit_breaker("external-api", failure_threshold=3)
        async def call_api():
            pass
    """
    breaker = CircuitBreakerRegistry.get_or_create(
        name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        **kwargs
    )
    return breaker
