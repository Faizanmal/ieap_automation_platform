"""
API Routes

Defines all API routes organized by domain.
"""

from fastapi import APIRouter

from .v1 import (
    analytics_router,
    auth_router,
    decisions_router,
    health_router,
    models_router,
    pipelines_router,
    predictions_router,
    tasks_router,
    webhooks_router,
)

# Main API router
api_router = APIRouter()

# API v1 routes
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

v1_router.include_router(health_router, prefix="/health", tags=["Health"])
v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
v1_router.include_router(models_router, prefix="/models", tags=["ML Models"])
v1_router.include_router(predictions_router, prefix="/predictions", tags=["Predictions"])
v1_router.include_router(pipelines_router, prefix="/pipelines", tags=["Data Pipelines"])
v1_router.include_router(decisions_router, prefix="/decisions", tags=["Decision Engine"])
v1_router.include_router(tasks_router, prefix="/tasks", tags=["Task Orchestrator"])
v1_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
v1_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])

# Include v1 router
api_router.include_router(v1_router)

# Legacy routes for backward compatibility (v0)
legacy_router = APIRouter(prefix="/api", tags=["Legacy (deprecated)"])

@legacy_router.get("/status", deprecated=True)
async def legacy_status():
    """Legacy status endpoint - use /api/v1/health instead"""
    return {"status": "ok", "message": "Use /api/v1/health for detailed health status"}

api_router.include_router(legacy_router)
