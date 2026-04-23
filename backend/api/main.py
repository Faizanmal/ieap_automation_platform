"""
FastAPI Application Factory

Enterprise-grade FastAPI application with comprehensive features.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
from .routes import api_router

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(APIError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id}
        )


class UnauthorizedError(APIError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(APIError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN"
        )


class ValidationError(APIError):
    def __init__(self, message: str, details: dict[str, Any]):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class RateLimitError(APIError):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


def create_app(
    title: str = "Intelligent Enterprise Automation Platform",
    version: str = "2.0.0",
    description: str = None,
    debug: bool = False,
    **kwargs
) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        title: API title
        version: API version
        description: API description
        debug: Enable debug mode
        **kwargs: Additional FastAPI arguments
        
    Returns:
        Configured FastAPI application
    """

    if description is None:
        description = """
# Intelligent Enterprise Automation Platform API

Enterprise-grade automation platform providing:

## 🤖 AI/ML Capabilities
- Multi-model ML predictions
- Autonomous decision making
- Real-time anomaly detection
- Predictive analytics

## 📊 Data Processing
- Real-time data pipelines
- ETL automation
- Data quality monitoring
- Stream processing

## 🔧 Orchestration
- Multi-agent coordination
- Workflow automation
- Task scheduling
- Resource optimization

## 🔐 Enterprise Security
- JWT & API key authentication
- Role-based access control
- Audit logging
- Data encryption

## 📈 Analytics & Reporting
- Interactive dashboards
- Custom reports
- Real-time metrics
- Executive summaries
"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan events"""
        logger.info("🚀 Starting IEAP API Gateway...")

        # Startup
        try:
            # Initialize components
            logger.info("Initializing platform components...")

            # You can initialize database connections, cache, etc. here
            # await init_database()
            # await init_cache()

            logger.info("✅ IEAP API Gateway started successfully")
            yield

        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            raise
        finally:
            # Shutdown
            logger.info("🛑 Shutting down IEAP API Gateway...")
            # await close_database()
            # await close_cache()
            logger.info("✅ IEAP API Gateway shutdown complete")

    # Create FastAPI app
    app = FastAPI(
        title=title,
        version=version,
        description=description,
        lifespan=lifespan,
        docs_url="/docs" if debug else "/api/docs",
        redoc_url="/redoc" if debug else "/api/redoc",
        openapi_url="/openapi.json" if debug else "/api/openapi.json",
        debug=debug,
        **kwargs
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if debug else [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://*.ieap.io"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    )

    # Add middleware (order matters - first added = last executed)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Add rate limiting in production
    if not debug:
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

    # Exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": exc.errors()}
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred" if not debug else str(exc)
                },
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    # Include routers
    app.include_router(api_router)

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """API root endpoint"""
        return {
            "name": title,
            "version": version,
            "status": "operational",
            "docs": "/api/docs",
            "health": "/api/v1/health"
        }

    return app


# Create default app instance
app = create_app()
