"""
Health API Router

FastAPI endpoints for health checks.
"""

import logging
from typing import Any

from fastapi import APIRouter, Query, Response

from .aggregator import HealthAggregator, HealthStatus

logger = logging.getLogger(__name__)

health_router = APIRouter(tags=["health"])

# Global health aggregator instance
_aggregator: HealthAggregator | None = None


def init_health_router(aggregator: HealthAggregator):
    """Initialize the health router with an aggregator"""
    global _aggregator
    _aggregator = aggregator


def get_aggregator() -> HealthAggregator:
    """Get the health aggregator"""
    if _aggregator is None:
        return HealthAggregator()
    return _aggregator


@health_router.get("/health")
async def health_check(
    response: Response,
    include_details: bool = Query(True),
    force_refresh: bool = Query(False)
) -> dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    Returns detailed health status of all components.
    """
    aggregator = get_aggregator()
    health = await aggregator.check_health(
        include_details=include_details,
        force_refresh=force_refresh
    )

    # Set appropriate status code
    if health.status == HealthStatus.UNHEALTHY:
        response.status_code = 503
    elif health.status == HealthStatus.DEGRADED:
        response.status_code = 200  # Still operational

    return health.to_dict()


@health_router.get("/health/live")
async def liveness_check() -> dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns 200 if the application is running.
    Used by Kubernetes to determine if the pod should be restarted.
    """
    aggregator = get_aggregator()
    return {
        "status": "alive" if aggregator.get_liveness() else "dead",
        "checks": ["process_running"]
    }


@health_router.get("/health/ready")
async def readiness_check(response: Response) -> dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns 200 if the application can handle requests.
    Used by Kubernetes to determine if traffic should be routed to the pod.
    """
    aggregator = get_aggregator()
    ready = await aggregator.get_readiness()

    if not ready:
        response.status_code = 503

    return {
        "status": "ready" if ready else "not_ready",
        "checks": ["database", "cache", "dependencies"]
    }


@health_router.get("/health/startup")
async def startup_check(response: Response) -> dict[str, Any]:
    """
    Kubernetes startup probe endpoint.
    
    Returns 200 once the application has fully started.
    Used by Kubernetes to determine when liveness/readiness checks should begin.
    """
    aggregator = get_aggregator()
    health = await aggregator.check_health()

    # Consider started if at least critical components are healthy
    started = health.status != HealthStatus.UNHEALTHY

    if not started:
        response.status_code = 503

    return {
        "status": "started" if started else "starting",
        "healthy_components": health.healthy_count,
        "total_components": len(health.components)
    }


@health_router.get("/health/components")
async def list_components() -> dict[str, Any]:
    """List all registered health check components"""
    aggregator = get_aggregator()
    tree = await aggregator.get_dependency_tree()
    return {
        "components": tree,
        "total": len(tree)
    }


@health_router.get("/health/components/{component_name}")
async def check_component(
    component_name: str,
    response: Response,
    force_refresh: bool = Query(False)
) -> dict[str, Any]:
    """Check health of a specific component"""
    aggregator = get_aggregator()
    health = await aggregator.check_component(component_name, force_refresh)

    if health.status == HealthStatus.UNHEALTHY:
        response.status_code = 503
    elif health.status == HealthStatus.UNKNOWN:
        response.status_code = 404

    return health.to_dict()


@health_router.get("/health/dependencies")
async def get_dependencies() -> dict[str, Any]:
    """Get dependency tree for all components"""
    aggregator = get_aggregator()
    return await aggregator.get_dependency_tree()


# Additional diagnostic endpoints
@health_router.get("/health/metrics")
async def health_metrics() -> dict[str, Any]:
    """Get health check metrics"""
    aggregator = get_aggregator()
    health = await aggregator.check_health()

    return {
        "total_checks": len(health.components),
        "healthy": health.healthy_count,
        "degraded": health.degraded_count,
        "unhealthy": health.unhealthy_count,
        "check_duration_ms": health.check_duration_ms,
        "status_distribution": {
            "healthy_pct": round(
                (health.healthy_count / len(health.components)) * 100, 1
            ) if health.components else 0,
            "degraded_pct": round(
                (health.degraded_count / len(health.components)) * 100, 1
            ) if health.components else 0,
            "unhealthy_pct": round(
                (health.unhealthy_count / len(health.components)) * 100, 1
            ) if health.components else 0
        }
    }
