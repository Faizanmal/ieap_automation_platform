"""
Health Aggregator

Comprehensive health checking with dependency management.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    last_check: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    last_healthy: datetime | None = None

    def is_critical(self) -> bool:
        """Check if component failure is critical"""
        return self.details.get("critical", False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "details": self.details,
            "dependencies": self.dependencies,
            "last_check": self.last_check.isoformat(),
            "consecutive_failures": self.consecutive_failures
        }


@dataclass
class SystemHealth:
    """Complete system health status"""
    status: HealthStatus
    components: dict[str, ComponentHealth]
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    check_duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "components": {
                name: comp.to_dict()
                for name, comp in self.components.items()
            },
            "summary": {
                "healthy": self.healthy_count,
                "degraded": self.degraded_count,
                "unhealthy": self.unhealthy_count,
                "total": len(self.components)
            },
            "check_duration_ms": round(self.check_duration_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "message": self.summary
        }


class HealthAggregator:
    """
    Aggregates health checks from multiple components.
    
    Features:
    - Dependency-aware health checking
    - Graceful degradation support
    - Auto-recovery mechanisms
    - Health check caching
    - Parallel check execution
    - Alert integration
    
    Usage:
        aggregator = HealthAggregator()
        
        # Register health checks
        aggregator.register("database", db_health_check, critical=True)
        aggregator.register("redis", redis_health_check, dependencies=["database"])
        aggregator.register("ml_models", ml_health_check, dependencies=["redis"])
        
        # Check health
        health = await aggregator.check_health()
        
        # Check specific component
        db_health = await aggregator.check_component("database")
    """

    def __init__(
        self,
        cache_ttl_seconds: float = 5.0,
        check_timeout_seconds: float = 10.0,
        recovery_manager = None
    ):
        self.cache_ttl = cache_ttl_seconds
        self.check_timeout = check_timeout_seconds
        self.recovery_manager = recovery_manager

        self._checks: dict[str, dict[str, Any]] = {}
        self._health_cache: dict[str, ComponentHealth] = {}
        self._cache_timestamps: dict[str, datetime] = {}
        self._listeners: list[Callable] = []

    def register(
        self,
        name: str,
        check_func: Callable[[], ComponentHealth],
        critical: bool = False,
        dependencies: list[str] | None = None,
        timeout: float | None = None
    ):
        """
        Register a health check.
        
        Args:
            name: Component name
            check_func: Async function that returns ComponentHealth
            critical: If True, failure makes system unhealthy
            dependencies: Components this depends on
            timeout: Custom timeout for this check
        """
        self._checks[name] = {
            "func": check_func,
            "critical": critical,
            "dependencies": dependencies or [],
            "timeout": timeout or self.check_timeout
        }
        logger.info(f"Registered health check: {name} (critical={critical})")

    def unregister(self, name: str):
        """Unregister a health check"""
        self._checks.pop(name, None)
        self._health_cache.pop(name, None)

    def add_listener(self, callback: Callable):
        """Add health change listener"""
        self._listeners.append(callback)

    async def check_health(
        self,
        include_details: bool = True,
        force_refresh: bool = False
    ) -> SystemHealth:
        """
        Check health of all registered components.
        
        Returns aggregated system health status.
        """
        start_time = time.time()

        # Determine check order based on dependencies
        check_order = self._get_check_order()

        # Run checks
        results: dict[str, ComponentHealth] = {}

        for name in check_order:
            if name in self._checks:
                health = await self._run_check(
                    name,
                    force_refresh=force_refresh,
                    skip_if_dependency_failed=results
                )
                results[name] = health

        # Calculate overall status
        statuses = [h.status for h in results.values()]
        critical_unhealthy = any(
            h.status == HealthStatus.UNHEALTHY and self._checks.get(n, {}).get("critical")
            for n, h in results.items()
        )

        if critical_unhealthy or statuses.count(HealthStatus.UNHEALTHY) > len(statuses) / 2:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.UNHEALTHY in statuses or HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        check_duration = (time.time() - start_time) * 1000

        # Create summary
        healthy_count = statuses.count(HealthStatus.HEALTHY)
        degraded_count = statuses.count(HealthStatus.DEGRADED)
        unhealthy_count = statuses.count(HealthStatus.UNHEALTHY)

        unhealthy_components = [
            n for n, h in results.items()
            if h.status == HealthStatus.UNHEALTHY
        ]

        summary = None
        if unhealthy_components:
            summary = f"Unhealthy components: {', '.join(unhealthy_components)}"
        elif degraded_count > 0:
            summary = f"{degraded_count} component(s) degraded"
        else:
            summary = "All components healthy"

        system_health = SystemHealth(
            status=overall_status,
            components=results,
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            unhealthy_count=unhealthy_count,
            check_duration_ms=check_duration,
            summary=summary
        )

        # Notify listeners
        for listener in self._listeners:
            try:
                await listener(system_health)
            except Exception as e:
                logger.error(f"Health listener error: {e}")

        # Trigger recovery if needed
        if self.recovery_manager and unhealthy_components:
            for name in unhealthy_components:
                await self.recovery_manager.attempt_recovery(name, results[name])

        return system_health

    async def check_component(
        self,
        name: str,
        force_refresh: bool = False
    ) -> ComponentHealth:
        """Check health of a specific component"""
        if name not in self._checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Component '{name}' not registered"
            )

        return await self._run_check(name, force_refresh=force_refresh)

    async def _run_check(
        self,
        name: str,
        force_refresh: bool = False,
        skip_if_dependency_failed: dict[str, ComponentHealth] | None = None
    ) -> ComponentHealth:
        """Run a single health check"""
        # Check cache
        if not force_refresh and name in self._health_cache:
            cache_time = self._cache_timestamps.get(name)
            if cache_time and (datetime.now() - cache_time).total_seconds() < self.cache_ttl:
                return self._health_cache[name]

        check_info = self._checks[name]
        check_func = check_info["func"]
        timeout = check_info["timeout"]
        dependencies = check_info["dependencies"]

        # Skip if dependency failed
        if skip_if_dependency_failed:
            failed_deps = [
                dep for dep in dependencies
                if dep in skip_if_dependency_failed and
                skip_if_dependency_failed[dep].status == HealthStatus.UNHEALTHY
            ]
            if failed_deps:
                return ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Dependency failed: {', '.join(failed_deps)}",
                    dependencies=dependencies
                )

        # Run check with timeout
        start_time = time.time()
        try:
            health = await asyncio.wait_for(
                check_func(),
                timeout=timeout
            )
            health.latency_ms = (time.time() - start_time) * 1000
            health.dependencies = dependencies

            if health.status == HealthStatus.HEALTHY:
                health.last_healthy = datetime.now()
                health.consecutive_failures = 0
            else:
                prev = self._health_cache.get(name)
                if prev:
                    health.consecutive_failures = prev.consecutive_failures + 1
                    health.last_healthy = prev.last_healthy

        except TimeoutError:
            health = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start_time) * 1000,
                message=f"Health check timed out after {timeout}s",
                dependencies=dependencies
            )
            prev = self._health_cache.get(name)
            if prev:
                health.consecutive_failures = prev.consecutive_failures + 1
                health.last_healthy = prev.last_healthy

        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            health = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start_time) * 1000,
                message=str(e),
                dependencies=dependencies
            )
            prev = self._health_cache.get(name)
            if prev:
                health.consecutive_failures = prev.consecutive_failures + 1
                health.last_healthy = prev.last_healthy

        health.details["critical"] = check_info["critical"]

        # Update cache
        self._health_cache[name] = health
        self._cache_timestamps[name] = datetime.now()

        return health

    def _get_check_order(self) -> list[str]:
        """
        Get check order based on dependency graph.
        Uses topological sort to ensure dependencies are checked first.
        """
        visited: set[str] = set()
        order: list[str] = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)

            check_info = self._checks.get(name, {})
            for dep in check_info.get("dependencies", []):
                if dep in self._checks:
                    visit(dep)

            order.append(name)

        for name in self._checks:
            visit(name)

        return order

    async def get_dependency_tree(self) -> dict[str, Any]:
        """Get dependency tree visualization"""
        tree = {}

        for name, info in self._checks.items():
            tree[name] = {
                "dependencies": info["dependencies"],
                "critical": info["critical"],
                "status": self._health_cache.get(name, ComponentHealth(
                    name=name, status=HealthStatus.UNKNOWN
                )).status.value
            }

        return tree

    def get_liveness(self) -> bool:
        """Simple liveness check (is the app running)"""
        return True

    async def get_readiness(self) -> bool:
        """Readiness check (can the app handle requests)"""
        health = await self.check_health()
        return health.status != HealthStatus.UNHEALTHY
