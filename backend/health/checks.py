"""
Health Checks

Pre-built health checks for common components.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod

from .aggregator import ComponentHealth, HealthStatus

logger = logging.getLogger(__name__)


class HealthCheck(ABC):
    """Abstract base class for health checks"""

    def __init__(self, name: str, critical: bool = False):
        self.name = name
        self.critical = critical

    @abstractmethod
    async def check(self) -> ComponentHealth:
        """Perform health check"""

    async def __call__(self) -> ComponentHealth:
        """Allow using check as callable"""
        return await self.check()


class DatabaseHealthCheck(HealthCheck):
    """PostgreSQL database health check"""

    def __init__(
        self,
        session_factory,
        name: str = "database",
        critical: bool = True
    ):
        super().__init__(name, critical)
        self.session_factory = session_factory

    async def check(self) -> ComponentHealth:
        start = time.time()

        try:
            async with self.session_factory() as session:
                result = await session.execute("SELECT 1")
                await result.fetchone()

                # Get connection pool stats if available
                details = {}
                if hasattr(session.bind, "pool"):
                    pool = session.bind.pool
                    details = {
                        "pool_size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout()
                    }

                return ComponentHealth(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=(time.time() - start) * 1000,
                    details={"type": "postgresql", **details}
                )

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )


class RedisHealthCheck(HealthCheck):
    """Redis cache health check"""

    def __init__(
        self,
        redis_client,
        name: str = "redis",
        critical: bool = False
    ):
        super().__init__(name, critical)
        self.redis = redis_client

    async def check(self) -> ComponentHealth:
        start = time.time()

        try:
            await self.redis.ping()
            info = await self.redis.info()

            memory_used = info.get("used_memory_human", "0B")
            connected_clients = info.get("connected_clients", 0)

            return ComponentHealth(
                name=self.name,
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={
                    "version": info.get("redis_version", "unknown"),
                    "memory_used": memory_used,
                    "connected_clients": connected_clients,
                    "uptime_seconds": info.get("uptime_in_seconds", 0)
                }
            )

        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.DEGRADED,
                latency_ms=(time.time() - start) * 1000,
                message=str(e),
                details={"fallback": "memory cache active"}
            )


class HTTPHealthCheck(HealthCheck):
    """HTTP endpoint health check"""

    def __init__(
        self,
        url: str,
        name: str = "http",
        method: str = "GET",
        expected_status: int = 200,
        timeout: float = 5.0,
        critical: bool = False,
        headers: dict[str, str] | None = None
    ):
        super().__init__(name, critical)
        self.url = url
        self.method = method
        self.expected_status = expected_status
        self.timeout = timeout
        self.headers = headers or {}

    async def check(self) -> ComponentHealth:
        import httpx

        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    self.method,
                    self.url,
                    headers=self.headers
                )

                latency = (time.time() - start) * 1000

                if response.status_code == self.expected_status:
                    return ComponentHealth(
                        name=self.name,
                        status=HealthStatus.HEALTHY,
                        latency_ms=latency,
                        details={
                            "url": self.url,
                            "status_code": response.status_code
                        }
                    )
                return ComponentHealth(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=latency,
                    message=f"Unexpected status: {response.status_code}",
                    details={
                        "url": self.url,
                        "status_code": response.status_code,
                        "expected": self.expected_status
                    }
                )

        except Exception as e:
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e),
                details={"url": self.url}
            )


class MemoryHealthCheck(HealthCheck):
    """System memory health check"""

    def __init__(
        self,
        name: str = "memory",
        warning_threshold: float = 80.0,
        critical_threshold: float = 95.0,
        critical: bool = False
    ):
        super().__init__(name, critical)
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    async def check(self) -> ComponentHealth:
        import psutil

        memory = psutil.virtual_memory()
        percent_used = memory.percent

        if percent_used >= self.critical_threshold:
            status = HealthStatus.UNHEALTHY
            message = f"Critical memory usage: {percent_used:.1f}%"
        elif percent_used >= self.warning_threshold:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {percent_used:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = None

        return ComponentHealth(
            name=self.name,
            status=status,
            message=message,
            details={
                "percent_used": percent_used,
                "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "available_gb": round(memory.available / 1024 / 1024 / 1024, 2)
            }
        )


class DiskHealthCheck(HealthCheck):
    """Disk space health check"""

    def __init__(
        self,
        path: str = "/",
        name: str = "disk",
        warning_threshold: float = 80.0,
        critical_threshold: float = 95.0,
        critical: bool = False
    ):
        super().__init__(name, critical)
        self.path = path
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    async def check(self) -> ComponentHealth:
        import psutil

        disk = psutil.disk_usage(self.path)
        percent_used = disk.percent

        if percent_used >= self.critical_threshold:
            status = HealthStatus.UNHEALTHY
            message = f"Critical disk usage: {percent_used:.1f}%"
        elif percent_used >= self.warning_threshold:
            status = HealthStatus.DEGRADED
            message = f"High disk usage: {percent_used:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = None

        return ComponentHealth(
            name=self.name,
            status=status,
            message=message,
            details={
                "path": self.path,
                "percent_used": percent_used,
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            }
        )


class MLModelHealthCheck(HealthCheck):
    """ML model availability health check"""

    def __init__(
        self,
        model_registry,
        name: str = "ml_models",
        critical: bool = False
    ):
        super().__init__(name, critical)
        self.registry = model_registry

    async def check(self) -> ComponentHealth:
        start = time.time()

        try:
            # Check if models are loaded
            loaded_models = await self.registry.list_loaded_models()
            total_models = await self.registry.list_available_models()

            if len(loaded_models) == 0 and len(total_models) > 0:
                return ComponentHealth(
                    name=self.name,
                    status=HealthStatus.DEGRADED,
                    latency_ms=(time.time() - start) * 1000,
                    message="No models currently loaded",
                    details={
                        "loaded": 0,
                        "available": len(total_models)
                    }
                )

            return ComponentHealth(
                name=self.name,
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={
                    "loaded": len(loaded_models),
                    "available": len(total_models),
                    "models": loaded_models
                }
            )

        except Exception as e:
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )


class CeleryHealthCheck(HealthCheck):
    """Celery worker health check"""

    def __init__(
        self,
        celery_app,
        name: str = "celery",
        critical: bool = False
    ):
        super().__init__(name, critical)
        self.app = celery_app

    async def check(self) -> ComponentHealth:
        start = time.time()

        try:
            # Run in thread to avoid blocking
            import concurrent.futures

            def ping_workers():
                inspect = self.app.control.inspect()
                return inspect.ping()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(ping_workers)
                result = await asyncio.get_event_loop().run_in_executor(
                    None, future.result, 5.0
                )

            if not result:
                return ComponentHealth(
                    name=self.name,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=(time.time() - start) * 1000,
                    message="No workers responding"
                )

            workers = list(result.keys())

            return ComponentHealth(
                name=self.name,
                status=HealthStatus.HEALTHY,
                latency_ms=(time.time() - start) * 1000,
                details={
                    "workers": len(workers),
                    "worker_names": workers
                }
            )

        except Exception as e:
            return ComponentHealth(
                name=self.name,
                status=HealthStatus.DEGRADED,
                latency_ms=(time.time() - start) * 1000,
                message=str(e)
            )


def create_default_checks(
    db_session = None,
    redis_client = None,
    celery_app = None
) -> dict[str, HealthCheck]:
    """Create default health checks"""
    checks = {
        "memory": MemoryHealthCheck(),
        "disk": DiskHealthCheck()
    }

    if db_session:
        checks["database"] = DatabaseHealthCheck(db_session, critical=True)

    if redis_client:
        checks["redis"] = RedisHealthCheck(redis_client)

    if celery_app:
        checks["celery"] = CeleryHealthCheck(celery_app)

    return checks
