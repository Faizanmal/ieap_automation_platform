"""
Health Check System

Comprehensive health checks for all system components.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    status: HealthStatus
    message: str | None = None
    latency_ms: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "details": self.details,
            "checked_at": self.checked_at.isoformat()
        }


@dataclass
class SystemHealth:
    """Overall system health."""
    status: HealthStatus
    components: list[ComponentHealth]
    version: str
    uptime_seconds: float
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "components": [c.to_dict() for c in self.components],
            "checked_at": self.checked_at.isoformat()
        }


class HealthChecker:
    """
    Health check manager for system components.
    """

    def __init__(
        self,
        version: str = "1.0.0",
        start_time: datetime | None = None
    ):
        self.version = version
        self.start_time = start_time or datetime.utcnow()
        self._checks: dict[str, Callable] = {}
        self._last_results: dict[str, ComponentHealth] = {}

        # Register default checks
        self._register_default_checks()

    def _register_default_checks(self):
        """Register default health checks."""
        self.register("database", self._check_database)
        self.register("redis", self._check_redis)
        self.register("celery", self._check_celery)

    def register(
        self,
        name: str,
        check_fn: Callable,
        critical: bool = True
    ):
        """
        Register a health check.
        
        Args:
            name: Component name
            check_fn: Async function that returns ComponentHealth
            critical: If True, failure makes system unhealthy
        """
        self._checks[name] = {
            "fn": check_fn,
            "critical": critical
        }

    def unregister(self, name: str):
        """Unregister a health check."""
        self._checks.pop(name, None)

    async def check_component(self, name: str) -> ComponentHealth:
        """Check a single component."""
        if name not in self._checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Unknown component: {name}"
            )

        check = self._checks[name]
        start = datetime.utcnow()

        try:
            result = await check["fn"]()
            result.latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
            self._last_results[name] = result
            return result
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            result = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(datetime.utcnow() - start).total_seconds() * 1000
            )
            self._last_results[name] = result
            return result

    async def check_all(self) -> SystemHealth:
        """Run all health checks."""
        components = await asyncio.gather(
            *[self.check_component(name) for name in self._checks.keys()],
            return_exceptions=True
        )

        # Convert exceptions to unhealthy status
        results = []
        for i, comp in enumerate(components):
            name = list(self._checks.keys())[i]
            if isinstance(comp, Exception):
                results.append(ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(comp)
                ))
            else:
                results.append(comp)

        # Determine overall status
        overall_status = self._calculate_overall_status(results)

        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return SystemHealth(
            status=overall_status,
            components=results,
            version=self.version,
            uptime_seconds=uptime
        )

    def _calculate_overall_status(
        self,
        components: list[ComponentHealth]
    ) -> HealthStatus:
        """Calculate overall system status."""
        critical_unhealthy = False
        any_unhealthy = False
        any_degraded = False

        for comp in components:
            check = self._checks.get(comp.name, {})
            is_critical = check.get("critical", True)

            if comp.status == HealthStatus.UNHEALTHY:
                any_unhealthy = True
                if is_critical:
                    critical_unhealthy = True
            elif comp.status == HealthStatus.DEGRADED:
                any_degraded = True

        if critical_unhealthy:
            return HealthStatus.UNHEALTHY
        if any_unhealthy or any_degraded:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    async def liveness(self) -> bool:
        """
        Kubernetes liveness probe.
        Returns True if the application is running.
        """
        return True

    async def readiness(self) -> bool:
        """
        Kubernetes readiness probe.
        Returns True if the application is ready to serve traffic.
        """
        health = await self.check_all()
        return health.status != HealthStatus.UNHEALTHY

    # ========================================================================
    # Default Health Check Implementations
    # ========================================================================

    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        try:
            from database import get_database

            db = get_database()
            is_healthy = await db.health_check()

            if is_healthy:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection OK"
                )
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message="Database connection failed"
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database error: {e!s}"
            )

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis connectivity."""
        try:
            from cache import get_redis

            redis = get_redis()
            is_healthy = await redis.health_check()

            if is_healthy:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis connection OK"
                )
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message="Redis connection failed"
            )
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis error: {e!s}"
            )

    async def _check_celery(self) -> ComponentHealth:
        """Check Celery worker status."""
        try:
            from cache.celery_app import celery_app

            # Ping workers
            inspect = celery_app.control.inspect()
            stats = inspect.stats()

            if stats:
                worker_count = len(stats)
                return ComponentHealth(
                    name="celery",
                    status=HealthStatus.HEALTHY,
                    message=f"{worker_count} worker(s) active",
                    details={"workers": list(stats.keys())}
                )
            return ComponentHealth(
                name="celery",
                status=HealthStatus.DEGRADED,
                message="No Celery workers detected"
            )
        except Exception as e:
            return ComponentHealth(
                name="celery",
                status=HealthStatus.DEGRADED,
                message=f"Celery check failed: {e!s}"
            )


# Global health checker
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
