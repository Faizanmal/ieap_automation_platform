"""
API v1 Routes

All v1 API endpoints organized by domain.
"""

from .analytics import router as analytics_router
from .auth import router as auth_router
from .decisions import router as decisions_router
from .health import router as health_router
from .models import router as models_router
from .pipelines import router as pipelines_router
from .predictions import router as predictions_router
from .tasks import router as tasks_router
from .webhooks import router as webhooks_router

__all__ = [
    "analytics_router",
    "auth_router",
    "decisions_router",
    "health_router",
    "models_router",
    "pipelines_router",
    "predictions_router",
    "tasks_router",
    "webhooks_router"
]
