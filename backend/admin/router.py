"""
Admin API Router

FastAPI router for admin endpoints.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .analytics import SystemAnalytics, TimeRange
from .dashboard import AdminDashboard
from .operations import MaintenanceMode, SystemOperations

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["admin"])


# Request/Response Models
class MaintenanceModeRequest(BaseModel):
    mode: str = "soft"
    message: str = "System is under maintenance"
    notify_users: bool = True


class FeatureFlagRequest(BaseModel):
    flag_name: str
    enabled: bool


class CacheClearRequest(BaseModel):
    pattern: str | None = None
    confirm: bool = False


class BackupRequest(BaseModel):
    backup_type: str = "full"
    include_logs: bool = False


class RestoreRequest(BaseModel):
    backup_id: str
    confirm: bool = False


# Dependency to get admin services
def get_dashboard() -> AdminDashboard:
    return AdminDashboard()


def get_analytics() -> SystemAnalytics:
    return SystemAnalytics()


def get_operations() -> SystemOperations:
    return SystemOperations()


# Dashboard Endpoints
@admin_router.get("/dashboard")
async def get_dashboard_summary(
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """Get complete admin dashboard summary"""
    summary = await dashboard.get_summary()
    return {
        "status": summary.status.value,
        "components": [
            {
                "name": c.name,
                "status": c.status.value,
                "latency_ms": c.latency_ms,
                "message": c.message,
                "details": c.details
            }
            for c in summary.components
        ],
        "metrics": {
            "total_requests": summary.metrics.total_requests,
            "requests_per_minute": summary.metrics.requests_per_minute,
            "error_rate": summary.metrics.error_rate,
            "avg_latency_ms": summary.metrics.avg_latency_ms,
            "cpu_usage": summary.metrics.cpu_usage,
            "memory_usage": summary.metrics.memory_usage,
            "disk_usage": summary.metrics.disk_usage,
            "uptime_seconds": summary.metrics.uptime_seconds
        },
        "alerts": summary.alerts,
        "recent_events": summary.recent_events,
        "quick_stats": summary.quick_stats
    }


@admin_router.get("/system/info")
async def get_system_info(
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """Get detailed system information"""
    return await dashboard.get_system_info()


@admin_router.get("/system/config")
async def get_system_config(
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """Get current system configuration"""
    return await dashboard.get_configuration()


# Analytics Endpoints
@admin_router.get("/analytics/usage")
async def get_usage_analytics(
    time_range: str = Query("day", regex="^(hour|day|week|month|quarter|year)$"),
    analytics: SystemAnalytics = Depends(get_analytics)
) -> dict[str, Any]:
    """Get usage statistics"""
    return await analytics.get_usage_stats(TimeRange(time_range))


@admin_router.get("/analytics/performance")
async def get_performance_analytics(
    time_range: str = Query("day", regex="^(hour|day|week|month|quarter|year)$"),
    metric: str = Query("latency"),
    analytics: SystemAnalytics = Depends(get_analytics)
) -> dict[str, Any]:
    """Get performance trends"""
    return await analytics.get_performance_trends(TimeRange(time_range), metric)


@admin_router.get("/analytics/errors")
async def get_error_analytics(
    time_range: str = Query("day", regex="^(hour|day|week|month|quarter|year)$"),
    analytics: SystemAnalytics = Depends(get_analytics)
) -> dict[str, Any]:
    """Get error analysis"""
    return await analytics.get_error_analysis(TimeRange(time_range))


@admin_router.get("/analytics/users")
async def get_user_analytics(
    time_range: str = Query("week", regex="^(hour|day|week|month|quarter|year)$"),
    analytics: SystemAnalytics = Depends(get_analytics)
) -> dict[str, Any]:
    """Get user behavior analytics"""
    return await analytics.get_user_analytics(TimeRange(time_range))


@admin_router.get("/analytics/models")
async def get_model_analytics(
    time_range: str = Query("week", regex="^(hour|day|week|month|quarter|year)$"),
    analytics: SystemAnalytics = Depends(get_analytics)
) -> dict[str, Any]:
    """Get ML model analytics"""
    return await analytics.get_model_analytics(TimeRange(time_range))


@admin_router.get("/analytics/resources")
async def get_resource_analytics(
    time_range: str = Query("day", regex="^(hour|day|week|month|quarter|year)$"),
    analytics: SystemAnalytics = Depends(get_analytics)
) -> dict[str, Any]:
    """Get resource utilization metrics"""
    return await analytics.get_resource_utilization(TimeRange(time_range))


@admin_router.get("/analytics/report")
async def generate_analytics_report(
    time_range: str = Query("week", regex="^(hour|day|week|month|quarter|year)$"),
    sections: str | None = Query(None),
    analytics: SystemAnalytics = Depends(get_analytics)
) -> dict[str, Any]:
    """Generate comprehensive analytics report"""
    include_sections = sections.split(",") if sections else None
    return await analytics.generate_report(TimeRange(time_range), include_sections)


# User Management Endpoints
@admin_router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    active_only: bool = False,
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """List users with pagination"""
    return await dashboard.list_users(page, per_page, search, role, active_only)


@admin_router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """Get user details"""
    user = await dashboard.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@admin_router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    updates: dict[str, Any],
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """Update user"""
    return await dashboard.update_user(user_id, updates)


@admin_router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """Deactivate user account"""
    success = await dashboard.deactivate_user(user_id)
    return {"success": success}


# API Key Management
@admin_router.get("/api-keys")
async def list_api_keys(
    user_id: str | None = None,
    include_revoked: bool = False,
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> list[dict[str, Any]]:
    """List API keys"""
    return await dashboard.list_api_keys(user_id, include_revoked)


@admin_router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> dict[str, Any]:
    """Revoke an API key"""
    success = await dashboard.revoke_api_key(key_id)
    return {"success": success}


# Audit Logs
@admin_router.get("/audit-logs")
async def get_audit_logs(
    user_id: str | None = None,
    event_type: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    dashboard: AdminDashboard = Depends(get_dashboard)
) -> list[dict[str, Any]]:
    """Get audit logs"""
    return await dashboard.get_audit_logs(user_id=user_id, event_type=event_type, limit=limit)


# Operations Endpoints
@admin_router.get("/maintenance")
async def get_maintenance_status(
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Get maintenance mode status"""
    return await ops.get_maintenance_status()


@admin_router.post("/maintenance/enable")
async def enable_maintenance(
    request: MaintenanceModeRequest,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Enable maintenance mode"""
    mode = MaintenanceMode(request.mode)
    return await ops.enable_maintenance_mode(mode, request.message, request.notify_users)


@admin_router.post("/maintenance/disable")
async def disable_maintenance(
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Disable maintenance mode"""
    return await ops.disable_maintenance_mode()


# Cache Management
@admin_router.get("/cache/stats")
async def get_cache_stats(
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Get cache statistics"""
    return await ops.get_cache_stats()


@admin_router.post("/cache/clear")
async def clear_cache(
    request: CacheClearRequest,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Clear cache"""
    return await ops.clear_cache(request.pattern, request.confirm)


# Database Operations
@admin_router.get("/database/stats")
async def get_database_stats(
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Get database statistics"""
    return await ops.get_database_stats()


@admin_router.post("/database/vacuum")
async def run_database_vacuum(
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Run database vacuum"""
    return await ops.run_database_vacuum()


@admin_router.post("/database/migrations")
async def run_migrations(
    dry_run: bool = True,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Run database migrations"""
    return await ops.run_migrations(dry_run)


# Backup Management
@admin_router.get("/backups")
async def list_backups(
    limit: int = Query(10, ge=1, le=100),
    ops: SystemOperations = Depends(get_operations)
) -> list[dict[str, Any]]:
    """List available backups"""
    return await ops.list_backups(limit)


@admin_router.post("/backups")
async def create_backup(
    request: BackupRequest,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Create a new backup"""
    backup = await ops.create_backup(request.backup_type, request.include_logs)
    return {
        "backup_id": backup.backup_id,
        "type": backup.type,
        "size_bytes": backup.size_bytes,
        "created_at": backup.created_at.isoformat(),
        "location": backup.location,
        "status": backup.status
    }


@admin_router.post("/backups/restore")
async def restore_backup(
    request: RestoreRequest,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Restore from backup"""
    return await ops.restore_backup(request.backup_id, request.confirm)


# Feature Flags
@admin_router.get("/feature-flags")
async def get_feature_flags(
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, bool]:
    """Get feature flag states"""
    return await ops.get_feature_flags()


@admin_router.put("/feature-flags")
async def update_feature_flag(
    request: FeatureFlagRequest,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Update a feature flag"""
    return await ops.update_feature_flag(request.flag_name, request.enabled)


# Services
@admin_router.get("/services")
async def get_services_status(
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Get all services status"""
    return await ops.get_service_status()


@admin_router.get("/services/{service_name}")
async def get_service_status(
    service_name: str,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Get specific service status"""
    return await ops.get_service_status(service_name)


@admin_router.post("/services/{service_name}/restart")
async def restart_service(
    service_name: str,
    graceful: bool = True,
    ops: SystemOperations = Depends(get_operations)
) -> dict[str, Any]:
    """Restart a service"""
    return await ops.restart_service(service_name, graceful)


# Operation Log
@admin_router.get("/operations/log")
async def get_operation_log(
    limit: int = Query(50, ge=1, le=500),
    ops: SystemOperations = Depends(get_operations)
) -> list[dict[str, Any]]:
    """Get administrative operation log"""
    return await ops.get_operation_log(limit)
