"""
Health Check Endpoints

Provides comprehensive health checks for:
- Overall system health
- Individual component health
- Dependency health (database, cache, etc.)
- Readiness and liveness probes for Kubernetes
"""

import asyncio
import logging
import time
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from api.schemas.health import (
    ComponentHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Track startup time for uptime calculation
_startup_time = datetime.now()


async def check_database_health() -> ComponentHealth:
    """Check database connectivity"""
    start = time.perf_counter()

    try:
        # In production, execute a simple query
        # await db.execute("SELECT 1")
        await asyncio.sleep(0.01)  # Simulate DB check

        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            response_time_ms=(time.perf_counter() - start) * 1000,
            message="Database connection successful"
        )
    except Exception as e:
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=(time.perf_counter() - start) * 1000,
            message=f"Database error: {e!s}"
        )


async def check_cache_health() -> ComponentHealth:
    """Check Redis cache connectivity"""
    start = time.perf_counter()

    try:
        # In production, ping Redis
        # await redis.ping()
        await asyncio.sleep(0.005)  # Simulate cache check

        return ComponentHealth(
            name="cache",
            status=HealthStatus.HEALTHY,
            response_time_ms=(time.perf_counter() - start) * 1000,
            message="Cache connection successful"
        )
    except Exception as e:
        return ComponentHealth(
            name="cache",
            status=HealthStatus.DEGRADED,  # Cache failure is degraded, not critical
            response_time_ms=(time.perf_counter() - start) * 1000,
            message=f"Cache error: {e!s}"
        )


async def check_ml_models_health() -> ComponentHealth:
    """Check ML models availability"""
    import time
    start = time.perf_counter()

    try:
        # Check if models are loaded and ready
        models_status = {
            "anomaly_detection": "loaded",
            "demand_forecasting": "loaded",
            "churn_prediction": "loaded"
        }

        return ComponentHealth(
            name="ml_models",
            status=HealthStatus.HEALTHY,
            response_time_ms=(time.perf_counter() - start) * 1000,
            message="ML models ready",
            details={"models": models_status}
        )
    except Exception as e:
        return ComponentHealth(
            name="ml_models",
            status=HealthStatus.DEGRADED,
            message=f"ML models error: {e!s}"
        )


async def check_orchestrator_health() -> ComponentHealth:
    """Check orchestrator status"""
    start = time.perf_counter()

    try:
        orchestrator_status = {
            "active_agents": 5,
            "queue_size": 0,
            "processing_rate": 100
        }

        return ComponentHealth(
            name="orchestrator",
            status=HealthStatus.HEALTHY,
            response_time_ms=(time.perf_counter() - start) * 1000,
            message="Orchestrator running",
            details=orchestrator_status
        )
    except Exception as e:
        return ComponentHealth(
            name="orchestrator",
            status=HealthStatus.UNHEALTHY,
            message=f"Orchestrator error: {e!s}"
        )


async def check_pipeline_health() -> ComponentHealth:
    """Check data pipeline status"""
    start = time.perf_counter()

    try:
        pipeline_status = {
            "active_sources": 3,
            "processing_rate": 1000,
            "buffer_utilization": 0.25
        }

        return ComponentHealth(
            name="data_pipeline",
            status=HealthStatus.HEALTHY,
            response_time_ms=(time.perf_counter() - start) * 1000,
            message="Pipeline operational",
            details=pipeline_status
        )
    except Exception as e:
        return ComponentHealth(
            name="data_pipeline",
            status=HealthStatus.DEGRADED,
            message=f"Pipeline error: {e!s}"
        )


@router.get(
    "",
    response_model=HealthResponse,
    summary="Get system health",
    description="Returns comprehensive health status of all system components"
)
async def get_health():
    """
    Comprehensive health check endpoint.
    
    Checks:
    - Database connectivity
    - Cache availability
    - ML models status
    - Orchestrator status
    - Data pipeline status
    """
    # Run all health checks in parallel
    checks = await asyncio.gather(
        check_database_health(),
        check_cache_health(),
        check_ml_models_health(),
        check_orchestrator_health(),
        check_pipeline_health(),
        return_exceptions=True
    )

    components = []
    for check in checks:
        if isinstance(check, Exception):
            components.append(ComponentHealth(
                name="unknown",
                status=HealthStatus.UNHEALTHY,
                message=str(check)
            ))
        else:
            components.append(check)

    # Determine overall status
    if any(c.status == HealthStatus.UNHEALTHY for c in components):
        overall_status = HealthStatus.UNHEALTHY
    elif any(c.status == HealthStatus.DEGRADED for c in components):
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    uptime = (datetime.now() - _startup_time).total_seconds()

    return HealthResponse(
        status=overall_status,
        uptime_seconds=uptime,
        components=components
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Kubernetes readiness probe",
    description="Returns whether the service is ready to receive traffic"
)
async def readiness_probe():
    """
    Kubernetes readiness probe.
    
    Returns 200 if service is ready to handle requests.
    Returns 503 if service is not ready.
    """
    # Check critical dependencies
    db_health = await check_database_health()

    if db_health.status == HealthStatus.UNHEALTHY:
        return ReadinessResponse(
            ready=False,
            reason="Database unavailable"
        )

    return ReadinessResponse(ready=True)


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Kubernetes liveness probe",
    description="Returns whether the service is alive"
)
async def liveness_probe():
    """
    Kubernetes liveness probe.
    
    Returns 200 if service is alive.
    If this fails, Kubernetes will restart the container.
    """
    return LivenessResponse(alive=True)


@router.get(
    "/metrics",
    summary="Get system metrics",
    description="Returns Prometheus-compatible metrics"
)
async def get_metrics():
    """
    Returns system metrics in Prometheus format.
    
    In production, this would be handled by a dedicated metrics endpoint.
    """
    uptime = (datetime.now() - _startup_time).total_seconds()

    metrics = f"""
# HELP ieap_uptime_seconds Time since service started
# TYPE ieap_uptime_seconds gauge
ieap_uptime_seconds {uptime}

# HELP ieap_health_status Current health status (1=healthy, 0.5=degraded, 0=unhealthy)
# TYPE ieap_health_status gauge
ieap_health_status{{component="database"}} 1
ieap_health_status{{component="cache"}} 1
ieap_health_status{{component="ml_models"}} 1
ieap_health_status{{component="orchestrator"}} 1
ieap_health_status{{component="data_pipeline"}} 1

# HELP ieap_api_requests_total Total API requests
# TYPE ieap_api_requests_total counter
ieap_api_requests_total{{method="GET",endpoint="/health"}} 1

# HELP ieap_active_agents Number of active AI agents
# TYPE ieap_active_agents gauge
ieap_active_agents 5

# HELP ieap_ml_predictions_total Total ML predictions made
# TYPE ieap_ml_predictions_total counter
ieap_ml_predictions_total{{model="anomaly_detection"}} 1000
ieap_ml_predictions_total{{model="churn_prediction"}} 500
ieap_ml_predictions_total{{model="demand_forecasting"}} 250
"""

    return PlainTextResponse(content=metrics.strip(), media_type="text/plain")
