"""
Enterprise API Gateway

Production-ready FastAPI gateway with:
- API versioning
- Rate limiting
- Request validation
- OpenAPI documentation
- Middleware stack
- Error handling
- Health checks
"""

from .dependencies import (
    get_api_key,
    get_current_user,
    get_db_session,
    require_permission,
)
from .main import app, create_app
from .middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
from .routes import api_router

__all__ = [
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "RequestIdMiddleware",
    "SecurityHeadersMiddleware",
    "api_router",
    "app",
    "create_app",
    "get_api_key",
    "get_current_user",
    "get_db_session",
    "require_permission"
]
