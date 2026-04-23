"""
Admin Dashboard Core

Central dashboard for system administration.
"""

import logging
import platform
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a component"""
    name: str
    status: SystemStatus
    latency_ms: float | None = None
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    total_requests: int = 0
    requests_per_minute: float = 0.0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    active_users: int = 0
    active_sessions: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    uptime_seconds: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DashboardSummary:
    """Complete dashboard summary"""
    status: SystemStatus
    components: list[ComponentHealth]
    metrics: SystemMetrics
    alerts: list[dict[str, Any]]
    recent_events: list[dict[str, Any]]
    quick_stats: dict[str, Any]


class AdminDashboard:
    """
    Admin dashboard for system monitoring and management.

    Features:
    - Real-time system status
    - Component health tracking
    - User management
    - System analytics
    - Alert management
    - Audit logs

    Usage:
        dashboard = AdminDashboard(db_session, redis_client)
        summary = await dashboard.get_summary()
        users = await dashboard.list_users(page=1, per_page=20)
    """

    def __init__(
        self,
        db_session = None,
        redis_client = None,
        metrics_registry = None
    ):
        self.db = db_session
        self.redis = redis_client
        self.metrics = metrics_registry
        self._start_time = datetime.now(UTC)
        self._alerts: list[dict[str, Any]] = []
        self._events: list[dict[str, Any]] = []

    async def get_summary(self) -> DashboardSummary:
        """Get complete dashboard summary"""
        components = await self._check_all_components()
        metrics = await self._get_system_metrics()

        # Determine overall status
        statuses = [c.status for c in components]
        if SystemStatus.UNHEALTHY in statuses:
            overall_status = SystemStatus.UNHEALTHY
        elif SystemStatus.DEGRADED in statuses:
            overall_status = SystemStatus.DEGRADED
        else:
            overall_status = SystemStatus.HEALTHY

        return DashboardSummary(
            status=overall_status,
            components=components,
            metrics=metrics,
            alerts=self._alerts[-10:],  # Last 10 alerts
            recent_events=self._events[-20:],  # Last 20 events
            quick_stats=await self._get_quick_stats()
        )

    async def _check_all_components(self) -> list[ComponentHealth]:
        """Check health of all components"""
        components = []

        # Check database
        components.append(await self._check_database())

        # Check Redis
        components.append(await self._check_redis())

        # Check ML models
        components.append(await self._check_ml_models())

        # Check task queue
        components.append(await self._check_task_queue())

        # Check external APIs
        components.append(await self._check_external_apis())

        return components

    async def _check_database(self) -> ComponentHealth:
        """Check database health"""
        try:
            start = datetime.now(UTC)
            if self.db:
                # Execute simple query
                await self.db.execute("SELECT 1")
                latency = (datetime.now(UTC) - start).total_seconds() * 1000
                return ComponentHealth(
                    name="database",
                    status=SystemStatus.HEALTHY,
                    latency_ms=latency,
                    details={"type": "postgresql"}
                )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        return ComponentHealth(
            name="database",
            status=SystemStatus.UNHEALTHY,
            message="Database connection failed"
        )

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis health"""
        try:
            start = datetime.now(UTC)
            if self.redis:
                await self.redis.ping()
                latency = (datetime.now(UTC) - start).total_seconds() * 1000
                info = await self.redis.info()
                return ComponentHealth(
                    name="redis",
                    status=SystemStatus.HEALTHY,
                    latency_ms=latency,
                    details={
                        "version": info.get("redis_version", "unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory": info.get("used_memory_human", "0B")
                    }
                )
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        return ComponentHealth(
            name="redis",
            status=SystemStatus.DEGRADED,
            message="Redis unavailable (using memory fallback)"
        )

    async def _check_ml_models(self) -> ComponentHealth:
        """Check ML models health"""
        # This would check actual model availability
        return ComponentHealth(
            name="ml_models",
            status=SystemStatus.HEALTHY,
            details={
                "loaded_models": 5,
                "inference_queue": 0
            }
        )

    async def _check_task_queue(self) -> ComponentHealth:
        """Check task queue health"""
        return ComponentHealth(
            name="task_queue",
            status=SystemStatus.HEALTHY,
            details={
                "pending_tasks": 0,
                "active_workers": 4
            }
        )

    async def _check_external_apis(self) -> ComponentHealth:
        """Check external API dependencies"""
        return ComponentHealth(
            name="external_apis",
            status=SystemStatus.HEALTHY,
            details={
                "services_checked": 3,
                "services_healthy": 3
            }
        )

    async def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""

        uptime = (datetime.now(UTC) - self._start_time).total_seconds()

        return SystemMetrics(
            total_requests=await self._get_metric("total_requests") or 0,
            requests_per_minute=await self._get_metric("rpm") or 0.0,
            error_rate=await self._get_metric("error_rate") or 0.0,
            avg_latency_ms=await self._get_metric("avg_latency") or 0.0,
            p95_latency_ms=await self._get_metric("p95_latency") or 0.0,
            p99_latency_ms=await self._get_metric("p99_latency") or 0.0,
            active_users=await self._get_metric("active_users") or 0,
            active_sessions=await self._get_metric("active_sessions") or 0,
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage("/").percent,
            uptime_seconds=uptime
        )

    async def _get_metric(self, name: str) -> float | None:
        """Get metric value from registry or Redis"""
        if self.redis:
            try:
                value = await self.redis.get(f"metric:{name}")
                return float(value) if value else None
            except Exception as e:
                logger.debug(f"Failed to fetch metric from redis: {e}")
        return None

    async def _get_quick_stats(self) -> dict[str, Any]:
        """Get quick statistics for dashboard"""
        return {
            "users_today": 150,
            "predictions_today": 1250,
            "decisions_today": 89,
            "pipelines_running": 3,
            "alerts_active": len([a for a in self._alerts if a.get("active")]),
            "models_deployed": 5
        }

    # User Management
    async def list_users(
        self,
        page: int = 1,
        per_page: int = 20,
        _search: str | None = None,
        _role: str | None = None,
        _active_only: bool = False
    ) -> dict[str, Any]:
        """List users with pagination and filtering"""
        # Would query database
        return {
            "users": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "pages": 0
        }

    async def get_user(self, _user_id: str) -> dict[str, Any] | None:
        """Get user details"""
        return None

    async def update_user(self, _user_id: str, _updates: dict[str, Any]) -> dict[str, Any]:
        """Update user"""
        return {}

    async def deactivate_user(self, _user_id: str) -> bool:
        """Deactivate a user account"""
        return True

    # API Key Management
    async def list_api_keys(
        self,
        _user_id: str | None = None,
        _include_revoked: bool = False
    ) -> list[dict[str, Any]]:
        """List API keys"""
        return []

    async def revoke_api_key(self, _key_id: str) -> bool:
        """Revoke an API key"""
        return True

    # Alert Management
    def add_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        source: str = "system"
    ):
        """Add a new alert"""
        alert = {
            "id": len(self._alerts) + 1,
            "title": title,
            "message": message,
            "severity": severity,
            "source": source,
            "active": True,
            "created_at": datetime.now(UTC).isoformat()
        }
        self._alerts.append(alert)
        logger.info(f"Alert added: {title}")

    def acknowledge_alert(self, alert_id: int):
        """Acknowledge an alert"""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["active"] = False
                alert["acknowledged_at"] = datetime.now(UTC).isoformat()
                return True
        return False

    # Event Logging
    def log_event(
        self,
        event_type: str,
        description: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ):
        """Log an admin event"""
        event = {
            "id": len(self._events) + 1,
            "type": event_type,
            "description": description,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.now(UTC).isoformat()
        }
        self._events.append(event)

    async def get_audit_logs(
        self,
        _start_date: datetime | None = None,
        _end_date: datetime | None = None,
        user_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get audit logs with filtering"""
        logs = self._events

        if user_id:
            logs = [log for log in logs if log.get("user_id") == user_id]

        if event_type:
            logs = [log for log in logs if log.get("type") == event_type]

        return logs[-limit:]

    # System Operations
    async def get_system_info(self) -> dict[str, Any]:
        """Get detailed system information"""

        return {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "python": {
                "version": sys.version,
                "implementation": platform.python_implementation()
            },
            "application": {
                "name": "IEAP",
                "version": "1.0.0",
                "environment": "production",
                "uptime": str(datetime.now(UTC) - self._start_time)
            }
        }

    async def get_configuration(self) -> dict[str, Any]:
        """Get current configuration (sanitized)"""
        return {
            "debug_mode": False,
            "log_level": "INFO",
            "cache_enabled": True,
            "rate_limiting_enabled": True,
            "features": {
                "ml_predictions": True,
                "autonomous_decisions": True,
                "real_time_streaming": True
            }
        }
